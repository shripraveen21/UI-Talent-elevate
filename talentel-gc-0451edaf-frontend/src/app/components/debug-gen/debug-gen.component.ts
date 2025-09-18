import { Component, OnInit } from '@angular/core';
import { environment } from '../../../environments/environment';
import { FormsModule } from '@angular/forms';
import { CommonModule } from '@angular/common';
import { Router, ActivatedRoute } from '@angular/router';
import { TechStackAgentService } from '../../services/techstack-agent/techstack-agent.service';
import { SharedDropdownComponent } from '../shared/shared-dropdown/shared-dropdown.component';

@Component({
    selector: 'app-debug-exercise',
    templateUrl: './debug-exercise.component.html',
    styleUrls: ['./debug-exercise.component.css'],
    imports: [FormsModule, CommonModule, SharedDropdownComponent]
})
export class DebugExerciseComponent implements OnInit {
    constructor(
        private router: Router,
        private route: ActivatedRoute,
        private techStackAgent: TechStackAgentService
    ) {}

    techStack = '';
    topics = '';

    readOnlyTechStack: string = '';
    readOnlyTopics: string[] = [];

    ngOnInit() {
        // Fetch tech stack and topics from sessionStorage
        const assessmentDetailsRaw = sessionStorage.getItem('assessmentDetails');
        if (assessmentDetailsRaw) {
            try {
                const details = JSON.parse(assessmentDetailsRaw);
                this.readOnlyTechStack = details.selectedTechStack?.name || '';
                this.readOnlyTopics = Array.isArray(details.selectedConcepts)
                    ? details.selectedConcepts.map((c: any) => c.name)
                    : [];
                this.techStack = this.readOnlyTechStack;
                this.topics = this.readOnlyTopics.join(',');
            } catch (e) {
                this.readOnlyTechStack = '';
                this.readOnlyTopics = [];
                this.techStack = '';
                this.topics = '';
            }
        }

        // If you still need to fetch techStacks for other logic, keep this:
        this.isLoadingTechStacks = true;
        this.techStackAgent.getTechStacks().subscribe({
            next: (data: any) => {
                this.techStacks = Array.isArray(data)
                    ? data.map((stack: any) => ({
                        id: stack.id,
                        name: stack.name
                    }))
                    : [];
                this.isLoadingTechStacks = false;
            },
            error: (err) => {
                this.techStackError = 'Failed to load tech stacks.';
                this.isLoadingTechStacks = false;
            }
        });
    }
    difficulty = 'intermediate';
    duration = 1;

    techStacks: any[] = [];
    selectedTechStack: any = null;
    isLoadingTechStacks = false;
    techStackError: string | null = null;

    difficultyLevels = [
        { id: 'beginner', name: 'Beginner' },
        { id: 'intermediate', name: 'Intermediate' },
        { id: 'advanced', name: 'Advanced' }
    ];
    selectedDifficultyLevel: any = { id: 'intermediate', name: 'Intermediate' };

    onDifficultyChange(selected: any) {
        this.selectedDifficultyLevel = selected;
        this.difficulty = selected ? selected.id : 'intermediate';
    }

    onTechStackChange(selected: any) {
        this.selectedTechStack = selected;
        this.techStack = selected ? selected.name : '';
    }

    status = '';
    brd = '';
    initialTopics: string[] = [];
    suggestedTopics: string[] = [];
    finalTopics: string[] = [];
    projectInfo: any = null;
    loading = false;
    
    // Feedback functionality properties - aligned with hands-on patterns
    userFeedback: string = '';
    isProcessing: boolean = false;
    
    // Enhanced state management following hands-on patterns
    regenerationCount: number = 0;
    maxRegenerations: number = 3;
    feedbackError: string | null = null;
    
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
        this.loading = true; // Set loading to true when starting exercise

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
                    this.loading = false; // Set loading to false on error
                    // Don't close WebSocket connection - allow retry
                }
            };

            this.ws.onmessage = (event) => {
                console.log('[DebugGen] WebSocket onmessage:', event);
                try {
                    const data = JSON.parse(event.data);
                    console.log('[DebugGen] data.type:', data.type);
                    if (data.type === 'error') {
                        this.status = data.content;
                        this.loading = false; // Set loading to false on error
                        this.isProcessing = false; // Reset processing state
                        // Don't close WebSocket connection on error - allow retry
                    } else if (data.type === 'brd_review') {
                        this.brd = data.brd;
                        console.log(data.type)
                        this.initialTopics = data.initial_topics;
                        this.suggestedTopics = data.suggested_topics.map((t: any) => t.topic);
                        this.status = 'Please review the generated BRD and select your final topics to proceed.';
                        this.loading = false; // Set loading to false when BRD is ready
                        this.isProcessing = false; // Reset processing state
                    } else if (data.type === 'brd_updated') {
                        // Handle updated BRD from feedback
                        this.brd = data.brd;
                        this.initialTopics = data.initial_topics || this.initialTopics;
                        this.suggestedTopics = data.suggested_topics ? data.suggested_topics.map((t: any) => t.topic) : this.suggestedTopics;
                        this.status = 'BRD updated based on your feedback. Please review and proceed.';
                        this.isProcessing = false;
                        this.userFeedback = ''; // Clear feedback after successful update
                    } else if (data.type === 'project_generated') {
                        this.projectInfo = data;
                        this.status = 'Project generated successfully! Injecting debugging challenges...';
                    } else if (data.type === 'status') {
                        this.status = data.content;
                    } else if (data.type === 'final_id') {
                        sessionStorage.setItem("debug_id", data.debug_exercise);
                        console.log('[DebugGen] debug_id stored in sessionStorage:', data.debug_exercise);
                        // Close WebSocket connection only after workflow completion
                        this.status = 'Debug exercise generated successfully! Redirecting...';
                        this.isProcessing = false;
                        // Close connection and navigate to next step
                        if (this.ws) {
                            this.ws.close();
                        }
                        // Navigate to debug results or next workflow step
                        setTimeout(() => {
                            this.goToNextWorkflowStep();
                        }, 1000);
                    } else {
                        this.status = 'Received an unexpected message from the server. Please contact support if this persists.';
                    }
                } catch (parseErr) {
                    this.status = 'There was a problem processing the server response. Please try again or contact support.';
                    this.isProcessing = false; // Reset processing state on parse error
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
                final_topics: selectedTopics,
                feedback: this.userFeedback // Include user feedback in the submission
            }));
            this.status = 'Final topics submitted! Generating your project...';
            this.goToNextWorkflowStep();
        } catch (err) {
            this.status = 'Could not send your selected topics. Please retry.';
        }
    }

    /**
     * Regenerates the BRD completely with enhanced feedback loop following hands-on patterns
     */
    regenerateCompletely() {
        if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
            this.status = 'Cannot regenerate: Connection to server lost. Please restart the exercise.';
            return;
        }

        // Check regeneration limits following hands-on pattern
        if (this.regenerationCount >= this.maxRegenerations) {
            this.status = `Maximum regeneration attempts (${this.maxRegenerations}) reached. Please proceed with current BRD or restart.`;
            return;
        }

        this.isProcessing = true;
        this.regenerationCount++;
        this.status = `Regenerating BRD completely... (Attempt ${this.regenerationCount}/${this.maxRegenerations})`;
        this.feedbackError = null;

        try {
            // Send regenerate action following hands-on message structure
            this.ws.send(JSON.stringify({
                action: 'regenerate',
                final_topics: [...this.initialTopics, ...this.suggestedTopics],
                regen_count: this.regenerationCount,
                max_regen: this.maxRegenerations
            }));
        } catch (err) {
            console.error('[DebugGen] Error sending regenerate request:', err);
            this.status = 'Could not send regeneration request. Please retry.';
            this.isProcessing = false;
            this.feedbackError = 'Failed to send regeneration request';
        }
    }

    /**
     * Submits feedback to modify the current BRD via WebSocket following hands-on patterns
     */
    submitFeedback() {
        if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
            this.status = 'Cannot submit feedback: Connection to server lost. Please restart the exercise.';
            this.feedbackError = 'WebSocket connection lost';
            return;
        }

        if (!this.userFeedback.trim()) {
            this.status = 'Please provide feedback before submitting.';
            this.feedbackError = 'Feedback is required';
            return;
        }

        this.isProcessing = true;
        this.status = 'Processing your feedback and updating BRD...';
        this.feedbackError = null;

        try {
            // Send feedback following hands-on message structure
            this.ws.send(JSON.stringify({
                action: 'feedback',
                feedback: this.userFeedback,
                final_topics: [...this.initialTopics, ...this.suggestedTopics],
                suggestions: this.userFeedback.split(',').map(s => s.trim()).filter(s => s.length > 0)
            }));
        } catch (err) {
            console.error('[DebugGen] Error sending feedback:', err);
            this.status = 'Could not send feedback. Please retry.';
            this.isProcessing = false;
            this.feedbackError = 'Failed to send feedback to server';
        }
    }

    /**
     * Approve the current BRD and finalize the workflow following hands-on patterns
     * This method sends an 'approve' action to the backend to complete the BRD process
     */
    approveBRD(): void {
        if (this.isProcessing || !this.ws || this.ws.readyState !== WebSocket.OPEN) {
            console.warn('Cannot approve BRD: WebSocket not ready or already processing');
            this.feedbackError = 'Cannot approve at this time';
            return;
        }

        this.isProcessing = true;
        this.status = 'Approving BRD and finalizing workflow...';
        this.feedbackError = null;
        
        try {
            // Send approve action following hands-on message structure
            const approveMessage = {
                action: 'approve',
                final_topics: [...this.initialTopics, ...this.suggestedTopics]
            };
            
            console.log('[DebugGen] Sending approve message:', approveMessage);
            this.ws.send(JSON.stringify(approveMessage));
            
        } catch (error) {
            console.error('[DebugGen] Error approving BRD:', error);
            this.isProcessing = false;
            this.status = 'Error occurred while approving BRD. Please try again.';
            this.feedbackError = 'Failed to approve BRD';
        }
    }

    /**
     * Proceeds with the current BRD without modifications (legacy method)
     * Now redirects to approveBRD method for consistency
     */
    proceedWithCurrentBRD() {
        this.approveBRD();
    }
}
