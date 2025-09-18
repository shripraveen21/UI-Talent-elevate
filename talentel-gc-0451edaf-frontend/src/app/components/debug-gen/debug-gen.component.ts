import { Component, OnInit } from '@angular/core';
import { environment } from '../../../environments/environment';
import { FormsModule } from '@angular/forms';
import { CommonModule } from '@angular/common';
import { Router, ActivatedRoute } from '@angular/router';
import { SharedDropdownComponent } from '../shared/shared-dropdown/shared-dropdown.component';

@Component({
    selector: 'app-debug-exercise',
    templateUrl: './debug-exercise.component.html',
    styleUrls: ['./debug-exercise.component.css'],
    imports: [FormsModule, CommonModule, SharedDropdownComponent]
})
export class DebugExerciseComponent implements OnInit {
    constructor(private router: Router, private route: ActivatedRoute) {}
    
    // Component properties for data binding
    techStack = '';
    topics = '';
    difficulty = 'medium';
    duration = 60;

    // Query parameter data (similar to mcq-form component)
    params: any = {
        tech_stack: [],
        concepts: []
    };

    // Dropdown options for difficulty selection
    difficultyOptions = [
        { id: 'beginner', name: 'Beginner' },
        { id: 'intermediate', name: 'Intermediate' },
        { id: 'advanced', name: 'Advanced' }
    ];

    // UI State management for the three screens
    currentState: 'configuration' | 'review' | 'final' = 'configuration';
    isLoading: boolean = false;

    status = '';
    brd = '';
    initialTopics: string[] = [];
    suggestedTopics: string[] = [];
    finalTopics: string[] = [];
    projectInfo: any = null;

    ws: WebSocket | null = null;

    ngOnInit() {
        // First, try to load from query parameters (new pattern for consistency)
        this.loadFromQueryParams();
        
        // Then load from session storage if available (existing pattern)
        this.loadTestDetailsFromSession();
    }

    /**
     * Load data from query parameters (similar to mcq-form component)
     * This ensures consistency with create-assessment navigation pattern
     */
    loadFromQueryParams() {
        this.route.queryParams.subscribe(params => {
            console.log('[DebugGen] Query params received:', params);
            
            // Parse techStack from query parameters
            if (params['techStack']) {
                try {
                    const techStackData = JSON.parse(params['techStack']);
                    this.params.tech_stack = [techStackData];
                    this.techStack = techStackData.name || '';
                    console.log('[DebugGen] TechStack from query params:', this.params.tech_stack);
                } catch (error) {
                    console.error('[DebugGen] Error parsing techStack query param:', error);
                }
            }
            
            // Parse concepts from query parameters
            if (params['concepts']) {
                try {
                    const conceptsData = JSON.parse(params['concepts']);
                    this.params.concepts = conceptsData;
                    this.topics = conceptsData.map((concept: any) => concept.name).join(', ');
                    console.log('[DebugGen] Concepts from query params:', this.params.concepts);
                } catch (error) {
                    console.error('[DebugGen] Error parsing concepts query param:', error);
                }
            }
            
            // Parse difficulty from query parameters
            if (params['difficulty']) {
                this.difficulty = params['difficulty'];
                console.log('[DebugGen] Difficulty from query params:', this.difficulty);
            }
            
            // Parse duration from query parameters
            if (params['duration']) {
                this.duration = parseInt(params['duration']) || 60;
                console.log('[DebugGen] Duration from query params:', this.duration);
            }
        });
    }

    /**
     * Load assessment details from session storage to maintain data flow
     * This mirrors the pattern used in mcq-quiz component
     */
    loadTestDetailsFromSession() {
        // Get assessment details from sessionStorage (same as mcq-quiz pattern)
        const assessmentDetails = sessionStorage.getItem('assessmentDetails');
        if (assessmentDetails) {
            try {
                const details = JSON.parse(assessmentDetails);
                
                // Auto-populate techstack from stored data
                if (details.selectedTechStack) {
                    this.techStack = details.selectedTechStack.name || '';
                    console.log('[DebugGen] Auto-populated techStack:', this.techStack);
                }
                
                // Auto-populate topics from stored concepts
                if (details.selectedConcepts && details.selectedConcepts.length > 0) {
                    this.topics = details.selectedConcepts.map((concept: any) => concept.name).join(', ');
                    console.log('[DebugGen] Auto-populated topics:', this.topics);
                }
                
                console.log('[DebugGen] Successfully loaded assessment details from sessionStorage');
            } catch (error) {
                console.error('[DebugGen] Error loading assessment details from sessionStorage:', error);
                // Fallback: try to load from old testDetails format for backward compatibility
                this.loadLegacyTestDetails();
            }
        } else {
            console.warn('[DebugGen] No assessmentDetails found in sessionStorage');
            // Fallback: try to load from old testDetails format
            this.loadLegacyTestDetails();
        }
    }

    /**
     * Fallback method to load from legacy testDetails format
     * Maintains backward compatibility
     */
    private loadLegacyTestDetails() {
        const testDetails = sessionStorage.getItem('testDetails');
        if (testDetails) {
            try {
                const details = JSON.parse(testDetails);
                if (details.selectedTechStack && details.selectedTechStack.length > 0) {
                    this.techStack = details.selectedTechStack[0].name;
                }
                if (details.selectedConcepts && details.selectedConcepts.length > 0) {
                    this.topics = details.selectedConcepts.map((concept: any) => concept.name).join(', ');
                }
                console.log('[DebugGen] Loaded from legacy testDetails format');
            } catch (error) {
                console.error('[DebugGen] Error loading legacy test details:', error);
            }
        }
    }

    /**
     * Handle difficulty selection change from shared dropdown
     */
    onDifficultyChange(selectedOption: any) {
        this.difficulty = selectedOption.id;
    }

    /**
     * Get the selected difficulty option object for the dropdown
     */
    getSelectedDifficultyOption() {
        return this.difficultyOptions.find(option => option.id === this.difficulty) || null;
    }

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
        this.currentState = 'review';
        this.isLoading = true;
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
                
                // Use structured data from query params if available, otherwise use form inputs
                let techStackValue: string;
                let topicsArray: string[];
                
                if (this.params.tech_stack && this.params.tech_stack.length > 0) {
                    // Use tech stack from query parameters
                    techStackValue = this.params.tech_stack[0].name || this.params.tech_stack[0];
                } else {
                    // Use tech stack from form input
                    techStackValue = this.techStack;
                }
                
                if (this.params.concepts && this.params.concepts.length > 0) {
                    // Use concepts from query parameters
                    topicsArray = this.params.concepts.map((concept: any) => concept.name || concept);
                } else {
                    // Use topics from form input
                    topicsArray = this.topics.split(',').map(t => t.trim());
                }
                
                const data = JSON.stringify({
                    tech_stack: techStackValue,
                    topics: topicsArray,
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
                        this.isLoading = false;
                    } else if (data.type === 'project_generated') {
                        this.projectInfo = data;
                        this.status = 'Project generated successfully! Injecting debugging challenges...';
                    } else if (data.type === 'status') {
                        this.status = data.content;
                    } else if (data.type === 'final_id') {
                        sessionStorage.setItem("debug_id", data.debug_exercise);
                        console.log('[DebugGen] debug_id stored in sessionStorage:', data.debug_exercise);
                        this.currentState = 'final';
                        this.isLoading = false;
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

    /**
     * Confirms the selected topics and stores debug exercise ID in session storage
     * before proceeding to the next workflow step
     */
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
            
            // Store debug exercise ID in session storage for final assessment save
            const debugId = this.generateDebugId(); // You might get this from your backend response
            sessionStorage.setItem('debug_id', debugId);
            
            // Proceed to next workflow step
            this.goToNextWorkflowStep();
        } catch (err) {
            this.status = 'Could not send your selected topics. Please retry.';
        }
    }

    /**
     * Navigate back to configuration screen
     */
    goBack() {
        this.currentState = 'configuration';
        this.isLoading = false;
    }

    /**
     * Regenerate the exercise (restart the process)
     */
    regenerate() {
        this.currentState = 'configuration';
        this.isLoading = false;
        this.status = '';
        this.brd = '';
        this.initialTopics = [];
        this.suggestedTopics = [];
        this.finalTopics = [];
        this.projectInfo = null;
        if (this.ws) {
            this.ws.close();
        }
    }

    /**
     * Approve and save the exercise
     */
    approveAndSave() {
        // Store debug exercise ID in session storage for final assessment save
        const debugId = sessionStorage.getItem('debug_id') || this.generateDebugId();
        sessionStorage.setItem('debug_id', debugId);
        
        // Proceed to next workflow step
        this.goToNextWorkflowStep();
    }

    /**
     * Generate or retrieve debug exercise ID
     * This should ideally come from your backend after successful generation
     */
    private generateDebugId(): string {
        // This is a placeholder - replace with actual ID from backend response
        return 'debug_' + Date.now();
    }
}
