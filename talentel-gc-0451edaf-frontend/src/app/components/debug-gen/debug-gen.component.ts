import { Component } from '@angular/core';
import { environment } from '../../../environments/environment';
import { FormsModule } from '@angular/forms';
import { CommonModule } from '@angular/common';

@Component({
    selector: 'app-debug-exercise',
    templateUrl: './debug-exercise.component.html',
    styleUrls: ['./debug-exercise.component.css'],
    imports: [FormsModule, CommonModule]
})
export class DebugExerciseComponent {
    techStack = '';
    topics = '';
    difficulty = 'intermediate';
    duration = 1;

    status = '';
    brd = '';
    initialTopics: string[] = [];
    suggestedTopics: string[] = [];
    finalTopics: string[] = [];
    projectInfo: any = null;

    ws: WebSocket | null = null;

    startExercise() {
        this.status = 'Connecting to Debug Exercise Generator...';
        this.brd = '';
        this.initialTopics = [];
        this.suggestedTopics = [];
        this.finalTopics = [];
        this.projectInfo = null;

        try {
            const token = localStorage.getItem('token'); // Or your token source
            this.ws = new WebSocket(`${environment.websocketUrl}/ws/debug-gen-ws?token=${token}`);

            this.ws.onopen = () => {
                this.status = 'Connected! Preparing your exercise parameters...';
                const data = JSON.stringify({
                    tech_stack: this.techStack,
                    topics: this.topics.split(',').map(t => t.trim()),
                    difficulty: this.difficulty,
                    duration: this.duration
                });
                try {
                    console.log(`Sending data: `, data);
                    this.ws!.send(data);
                } catch (sendErr) {
                    this.status = 'Could not send your exercise details. Please retry.';
                    this.ws!.close();
                }
            };

            this.ws.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    if (data.type === 'error') {
                        this.status = data.content;
                        this.ws!.close();
                    } else if (data.type === 'brd_review') {
                        this.brd = data.brd;
                        this.initialTopics = data.initial_topics;
                        this.suggestedTopics = data.suggested_topics.map((t: any) => t.topic);
                        this.status = 'Please review the generated BRD and select your final topics to proceed.';
                    } else if (data.type === 'project_generated') {
                        this.projectInfo = data;
                        this.status = 'Project generated successfully! Injecting debugging challenges...';
                    } else if (data.type === 'status') {
                        this.status = data.content;
                    } else {
                        this.status = 'Received an unexpected message from the server. Please contact support if this persists.';
                    }
                } catch (parseErr) {
                    this.status = 'There was a problem processing the server response. Please try again or contact support.';
                }
            };

            this.ws.onerror = (event) => {
                this.status = 'A connection error occurred. Please refresh the page or check your internet connection.';
            };

            this.ws.onclose = (event) => {
                if (event.code !== 1000) { // 1000 means normal closure
                    this.status = `Connection closed unexpectedly (code: ${event.code}). Please retry or contact support.`;
                } else {
                    this.status = 'Connection closed.';
                }
            };

        } catch (err) {
            this.status = 'Unable to connect to the server. Please check your network and try again.';
        }
    }

    confirmTopics() {
        if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
            this.status = 'Cannot confirm topics: Connection to server lost. Please restart the exercise.';
            return;
        }
        try {
            const selectedTopics = [...this.initialTopics, ...this.suggestedTopics];
            this.finalTopics = selectedTopics;
            this.ws.send(JSON.stringify({
                final_topics: selectedTopics
            }));
            this.status = 'Final topics submitted! Generating your project...';
        } catch (err) {
            this.status = 'Could not send your selected topics. Please retry.';
        }
    }
}
