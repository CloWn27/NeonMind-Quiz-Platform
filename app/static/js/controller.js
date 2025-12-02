/**
 * Game Controller - Smartphone View
 * Features: Wake Lock API, SocketIO, Reconnection Support
 */

class GameController {
    constructor(roomCode, userId) {
        this.roomCode = roomCode;
        this.userId = userId;
        this.socket = null;
        this.wakeLock = null;
        this.currentQuestion = null;
        this.questionStartTime = null;
        this.timerInterval = null;
        
        // Stats
        this.score = 0;
        this.streak = 0;
        this.level = 1;
    }
    
    async init() {
        // Request Wake Lock
        await this.requestWakeLock();
        
        // Connect to SocketIO
        this.connectSocket();
        
        // Handle visibility change (reconnection)
        document.addEventListener('visibilitychange', () => {
            if (!document.hidden) {
                this.handleReconnect();
            }
        });
    }
    
    async requestWakeLock() {
        if ('wakeLock' in navigator) {
            try {
                this.wakeLock = await navigator.wakeLock.request('screen');
                console.log('Wake Lock active');
                document.getElementById('wakeLockIndicator').classList.remove('hidden');
                
                this.wakeLock.addEventListener('release', () => {
                    console.log('Wake Lock released');
                    document.getElementById('wakeLockIndicator').classList.add('hidden');
                });
            } catch (err) {
                console.error('Wake Lock error:', err);
            }
        }
    }
    
    connectSocket() {
        this.socket = io();
        
        this.socket.on('connect', () => {
            console.log('Connected to server');
            this.socket.emit('join_game', { room_code: this.roomCode });
        });
        
        this.socket.on('room_state', (data) => {
            console.log('Room state:', data);
        });
        
        this.socket.on('new_question', (data) => {
            this.handleNewQuestion(data);
        });
        
        this.socket.on('answer_result', (data) => {
            this.handleAnswerResult(data);
        });
        
        this.socket.on('game_finished', (data) => {
            this.handleGameFinished(data);
        });
        
        this.socket.on('jammer_attack', (data) => {
            this.handleJammerAttack(data);
        });
        
        this.socket.on('kicked', () => {
            alert('Du wurdest vom Admin aus dem Spiel entfernt');
            window.location.href = '/';
        });
        
        this.socket.on('error', (data) => {
            console.error('Socket error:', data.message);
        });
    }
    
    handleReconnect() {
        if (this.socket && !this.socket.connected) {
            this.socket.emit('reconnect_game', { room_code: this.roomCode });
        }
    }
    
    handleNewQuestion(data) {
        this.currentQuestion = data;
        this.questionStartTime = Date.now();
        
        // Hide waiting/result screens
        document.getElementById('waitingScreen').classList.add('hidden');
        document.getElementById('resultScreen').classList.add('hidden');
        
        // Show question screen
        const questionScreen = document.getElementById('questionScreen');
        questionScreen.classList.remove('hidden');
        
        // Update question text
        document.getElementById('questionText').innerText = data.frage_text;
        
        // Show code snippet if exists
        const codeSnippet = document.getElementById('codeSnippet');
        if (data.code_snippet) {
            codeSnippet.innerText = data.code_snippet;
            codeSnippet.classList.remove('hidden');
        } else {
            codeSnippet.classList.add('hidden');
        }
        
        // Render answers
        this.renderAnswers(data.antworten);
        
        // Start timer
        this.startTimer(data.zeit_sekunden);
    }
    
    renderAnswers(antworten) {
        const container = document.getElementById('answersContainer');
        container.innerHTML = '';
        
        antworten.forEach((antwort, index) => {
            const button = document.createElement('button');
            button.className = 'cyber-button w-full text-left p-6 hover:scale-105 transition-transform';
            button.innerHTML = `
                <span class="text-cyber-pink font-bold mr-4">${String.fromCharCode(65 + index)}</span>
                ${antwort.text}
            `;
            button.onclick = () => this.submitAnswer(antwort.id);
            container.appendChild(button);
        });
    }
    
    startTimer(seconds) {
        let remaining = seconds;
        const timerBar = document.getElementById('timerBar');
        const timeDisplay = document.getElementById('timeRemaining');
        
        // Clear existing interval
        if (this.timerInterval) {
            clearInterval(this.timerInterval);
        }
        
        this.timerInterval = setInterval(() => {
            remaining--;
            const percentage = (remaining / seconds) * 100;
            timerBar.style.width = percentage + '%';
            timeDisplay.innerText = remaining + 's';
            
            if (remaining <= 0) {
                clearInterval(this.timerInterval);
                this.handleTimeout();
            }
        }, 1000);
    }
    
    submitAnswer(answerId) {
        if (!this.currentQuestion) return;
        
        // Calculate time taken
        const timeTaken = (Date.now() - this.questionStartTime) / 1000;
        
        // Disable all answer buttons
        const buttons = document.querySelectorAll('#answersContainer button');
        buttons.forEach(btn => btn.disabled = true);
        
        // Stop timer
        if (this.timerInterval) {
            clearInterval(this.timerInterval);
        }
        
        // Send answer to server
        this.socket.emit('submit_answer', {
            room_code: this.roomCode,
            answer_id: answerId,
            time_taken: timeTaken
        });
    }
    
    handleTimeout() {
        // Show timeout message
        document.getElementById('questionScreen').classList.add('hidden');
        document.getElementById('resultScreen').classList.remove('hidden');
        document.getElementById('resultIcon').innerText = '⏱️';
        document.getElementById('resultText').innerText = 'Zeit abgelaufen!';
        document.getElementById('resultDetails').innerText = '';
        
        setTimeout(() => {
            document.getElementById('resultScreen').classList.add('hidden');
            document.getElementById('waitingScreen').classList.remove('hidden');
        }, 3000);
    }
    
    handleAnswerResult(data) {
        // Update stats
        this.score = data.total_score;
        this.streak = data.streak;
        if (data.level) {
            this.level = data.level;
        }
        
        document.getElementById('playerScore').innerText = this.score;
        document.getElementById('playerStreak').innerText = this.streak;
        document.getElementById('playerLevel').innerText = this.level;
        
        // Show result
        document.getElementById('questionScreen').classList.add('hidden');
        const resultScreen = document.getElementById('resultScreen');
        resultScreen.classList.remove('hidden');
        
        if (data.correct) {
            document.getElementById('resultIcon').innerText = '✅';
            document.getElementById('resultText').innerText = 'RICHTIG!';
            document.getElementById('resultText').className = 'text-3xl font-bold mb-4 neon-text';
            
            let details = `+${data.score} Punkte`;
            if (data.leveled_up) {
                details += ` | 🎉 LEVEL UP! Level ${data.level}`;
            }
            if (data.xp_gained) {
                details += ` | +${data.xp_gained} XP`;
            }
            document.getElementById('resultDetails').innerText = details;
        } else {
            document.getElementById('resultIcon').innerText = '❌';
            document.getElementById('resultText').innerText = 'FALSCH!';
            document.getElementById('resultText').className = 'text-3xl font-bold mb-4 neon-pink-text';
            
            if (data.eliminated) {
                document.getElementById('resultDetails').innerText = '💀 Du wurdest eliminiert!';
            } else {
                document.getElementById('resultDetails').innerText = 'Streak zurückgesetzt';
            }
        }
        
        // Hide result after 3 seconds
        setTimeout(() => {
            if (!data.eliminated) {
                resultScreen.classList.add('hidden');
                document.getElementById('waitingScreen').classList.remove('hidden');
            }
        }, 3000);
    }
    
    handleGameFinished(data) {
        // Show final screen
        document.getElementById('questionScreen').classList.add('hidden');
        document.getElementById('resultScreen').classList.add('hidden');
        document.getElementById('waitingScreen').classList.add('hidden');
        
        const finishedScreen = document.getElementById('finishedScreen');
        finishedScreen.classList.remove('hidden');
        
        document.getElementById('finalScore').innerText = this.score;
        document.getElementById('finalStreak').innerText = this.streak;
        
        // Release wake lock
        if (this.wakeLock) {
            this.wakeLock.release();
        }
    }
    
    handleJammerAttack(data) {
        // Apply glitch effect
        const app = document.getElementById('controllerApp');
        app.classList.add('glitch-effect');
        
        // Add visual distortion
        app.style.filter = 'hue-rotate(180deg) saturate(3)';
        
        setTimeout(() => {
            app.classList.remove('glitch-effect');
            app.style.filter = '';
        }, data.duration || 3000);
    }
}
