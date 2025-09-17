import { Component } from '@angular/core';
import { environment } from '../../../environments/environment';
import { FormsModule } from '@angular/forms';
import { CommonModule } from '@angular/common';
import { Router, ActivatedRoute } from '@angular/router';

@Component({
    selector: 'app-debug-exercise',
    templateUrl: './debug-exercise.component.html',
    styleUrls: ['./debug-exercise.component.css'],
    imports: [FormsModule, CommonModule]
})
export class DebugExerciseComponent {
    constructor(private router: Router, private route: ActivatedRoute) {}
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

    /**
     * Advances the workflow to the next step based on the sequence in sessionStorage.
     * If at the end, navigates to assessment save or dashboard.
     */
    goToNextWorkflowStep() {
        const workflowSequenceRaw = sessionStorage.getItem('workflowSequence');
        const currentStepRaw = sessionStorage.getItem('currentWorkflowStep');
        let workflowSequence: string[] = [];
        let currentStep = 0;

        if (workflowSequenceRaw) {
            try {
                workflowSequence = JSON.parse(workflowSequenceRaw);
            } catch (e) {
                workflowSequence = [];
            }
        }

        if (currentStepRaw) {
            currentStep = Number(currentStepRaw);
        }

        const nextStep = currentStep + 1;
        sessionStorage.setItem('currentWorkflowStep', nextStep.toString());

        if (workflowSequence && nextStep < workflowSequence.length) {
            const nextComponent = workflowSequence[nextStep];
            if (nextComponent === 'mcq') {
                this.router.navigate(['/mcq-quiz']);
            } else if (nextComponent === 'debug') {
                this.router.navigate(['/debug-gen']);
            } else if (nextComponent === 'handsOn') {
                this.router.navigate(['/handson-gen']);
            } else {
                // Unknown component, fallback to dashboard
                this.proceedToSaveAssessment();
            }
        } else {
            // End of workflow, go to save assessment step
            this.proceedToSaveAssessment();
        }
    }

    proceedToSaveAssessment() {
    this.router.navigate(['/create-assessment'], {
      queryParams: { step: 'save' }
    });
  }

startExercise() {
        console.log('[DebugGen] startExercise called');
        this.status = 'Connecting to Debug Exercise Generator...';
        this.brd = '';
        this.initialTopics = [];
        this.suggestedTopics = [];
        this.finalTopics = [];
        this.projectInfo = null;

        try {
            const token = localStorage.getItem('token'); // Or your token source
            console.log('[DebugGen] Using token:', token);
            const wsUrl = `${environment.websocketUrl}/ws/debug-gen-ws?token=${token}`;
            console.log('[DebugGen] WebSocket URL:', wsUrl);
            this.ws = new WebSocket(wsUrl);

            this.ws.onopen = () => {
                console.log('[DebugGen] WebSocket onopen');
                this.status = 'Connected! Preparing your exercise parameters...';
                const data = JSON.stringify({
                    tech_stack: this.techStack,
                    topics: this.topics.split(',').map(t => t.trim()),
                    difficulty: this.difficulty,
                    duration: this.duration
                });
                try {
                    console.log('[DebugGen] Sending data:', data);
                    this.ws!.send(data);
                } catch (sendErr) {
                    console.error('[DebugGen] Send error:', sendErr);
                    this.status = 'Could not send your exercise details. Please retry.';
                    this.ws!.close();
                }
            };

            this.ws.onmessage = (event) => {
                console.log('[DebugGen] WebSocket onmessage:', event);
                try {
                    const data = JSON.parse(event.data);
                    console.log('[DebugGen] data.type:', data.type);
                    if (data.type === 'error') {
                        this.status = data.content;
                        this.ws!.close();
                    } else if (data.type === 'brd_review') {
                        this.brd = data.brd;
                        console.log(data.type)
                        this.initialTopics = data.initial_topics;
                        this.suggestedTopics = data.suggested_topics.map((t: any) => t.topic);
                        this.status = 'Please review the generated BRD and select your final topics to proceed.';
                    } else if (data.type === 'project_generated') {
                        this.projectInfo = data;
                        this.status = 'Project generated successfully! Injecting debugging challenges...';
                    } else if (data.type === 'status') {
                        this.status = data.content;
                    } else if (data.type === 'final_id') {
                        sessionStorage.setItem("debug_id", data.debug_exercise);
                        console.log('[DebugGen] debug_id stored in sessionStorage:', data.debug_exercise);
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
            console.error('[DebugGen] Exception in startExercise:', err);
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
            this.goToNextWorkflowStep();
        } catch (err) {
            this.status = 'Could not send your selected topics. Please retry.';
        }
    }
}
