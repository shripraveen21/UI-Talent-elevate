import { Component, OnInit } from '@angular/core';
import { HandsonAgentService, AgentMessage } from '../../services/hands-on.service';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router, ActivatedRoute } from '@angular/router';
import { SharedDropdownComponent } from '../shared/shared-dropdown/shared-dropdown.component';

@Component({
  selector: 'app-handson-workflow',
  templateUrl: './hands-on-gen.component.html',
  imports: [CommonModule, FormsModule, SharedDropdownComponent]
})
export class HandsonWorkflowComponent implements OnInit {
  // Component properties for data binding
  techStackName = '';
  difficulty = 'intermediate'; // Default difficulty level
  duration = 30;
  topics: string[] = [];
  topicsInput = '';

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

  // UI State management for loading and status (similar to debug-gen)
  isLoading: boolean = false;
  status = '';

  srsReview?: AgentMessage;
  finalData?: any;
  error?: string;
  handsonStored : boolean = false

  constructor(private handsonAgent: HandsonAgentService, private router: Router, private route: ActivatedRoute) { }

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
      console.log('[HandsOnGen] Query params received:', params);
      
      // Parse techStack from query parameters
      if (params['techStack']) {
        try {
          const techStackData = JSON.parse(params['techStack']);
          this.params.tech_stack = [techStackData];
          this.techStackName = techStackData.name || '';
          console.log('[HandsOnGen] TechStack from query params:', this.params.tech_stack);
        } catch (error) {
          console.error('[HandsOnGen] Error parsing techStack query param:', error);
        }
      }
      
      // Parse concepts from query parameters
      if (params['concepts']) {
        try {
          const conceptsData = JSON.parse(params['concepts']);
          this.params.concepts = conceptsData;
          this.topicsInput = conceptsData.map((concept: any) => concept.name).join(', ');
          console.log('[HandsOnGen] Concepts from query params:', this.params.concepts);
        } catch (error) {
          console.error('[HandsOnGen] Error parsing concepts query param:', error);
        }
      }
      
      // Force change detection to update the UI
      setTimeout(() => {
        console.log('[HandsOnGen] Final params state:', this.params);
        console.log('[HandsOnGen] Tech stack length:', this.params.tech_stack?.length);
        console.log('[HandsOnGen] Concepts length:', this.params.concepts?.length);
      }, 100);
    });
  }

  /**
   * Load test details from session storage to maintain data flow
   * Updated to use assessmentDetails pattern consistent with mcq-quiz and debug components
   */
  loadTestDetailsFromSession() {
    console.log('Loading test details from session storage for hands-on component...');
    
    // First try to load from assessmentDetails (new pattern)
    const assessmentDetails = sessionStorage.getItem('assessmentDetails');
    if (assessmentDetails) {
      try {
        const details = JSON.parse(assessmentDetails);
        console.log('Found assessmentDetails in sessionStorage:', details);
        
        if (details.selectedTechStack && details.selectedTechStack.length > 0) {
          this.techStackName = details.selectedTechStack[0].name;
          console.log('Set techStackName from assessmentDetails:', this.techStackName);
        }
        if (details.selectedConcepts && details.selectedConcepts.length > 0) {
          this.topicsInput = details.selectedConcepts.map((concept: any) => concept.name).join(', ');
          console.log('Set topicsInput from assessmentDetails:', this.topicsInput);
        }
        return; // Exit early if we found data
      } catch (error) {
        console.error('Error parsing assessmentDetails from session:', error);
      }
    }
    
    // Fallback to legacy testDetails pattern for backward compatibility
    this.loadLegacyTestDetails();
  }

  /**
   * Fallback method to load from legacy testDetails format
   * Maintains backward compatibility with older workflow patterns
   */
  private loadLegacyTestDetails() {
    console.log('Falling back to legacy testDetails pattern...');
    const testDetails = sessionStorage.getItem('testDetails');
    if (testDetails) {
      try {
        const details = JSON.parse(testDetails);
        console.log('Found legacy testDetails in sessionStorage:', details);
        
        if (details.selectedTechStack && details.selectedTechStack.length > 0) {
          this.techStackName = details.selectedTechStack[0].name;
          console.log('Set techStackName from legacy testDetails:', this.techStackName);
        }
        if (details.selectedConcepts && details.selectedConcepts.length > 0) {
          this.topicsInput = details.selectedConcepts.map((concept: any) => concept.name).join(', ');
          console.log('Set topicsInput from legacy testDetails:', this.topicsInput);
        }
      } catch (error) {
        console.error('Error loading legacy test details from session:', error);
      }
    } else {
      console.log('No test details found in sessionStorage');
    }
  }


  addTopic() {
    this.topics.push('');
  }

  removeTopic(i: number) {
    this.topics.splice(i, 1);
  }

  onSubmit() {
    // Set loading state and status message (similar to debug-gen)
    this.isLoading = true;
    this.status = 'Connecting to Hands-On Project Generator...';
    this.error = undefined; // Clear any previous errors
    
    // Use structured data from query params if available, otherwise use form inputs
    let techStackValue: string;
    let topicsArray: string[];
    
    if (this.params.tech_stack && this.params.tech_stack.length > 0) {
      // Use tech stack from query parameters
      techStackValue = this.params.tech_stack[0].name || this.params.tech_stack[0];
    } else {
      // Use tech stack from form input
      techStackValue = this.techStackName;
    }
    
    if (this.params.concepts && this.params.concepts.length > 0) {
      // Use concepts from query parameters
      topicsArray = this.params.concepts.map((concept: any) => concept.name || concept);
    } else {
      // Use topics from form input
      topicsArray = this.topicsInput.split(',').map(t => t.trim()).filter(t => t);
    }
    
    const params = {
      tech_stack: [{ name: techStackValue }],
      topics: topicsArray,
      duration: this.duration
    };
    
    console.log('[HandsOn] Sending params:', params);
    this.status = 'Generating SRS document...';
    
    this.handsonAgent.connect(params).subscribe(msg => {
      if (msg.type === 'srs_review') {
        this.srsReview = msg;
        this.isLoading = false;
        this.status = 'SRS generated successfully! Please review and approve.';
      } else if (msg.type === 'final') {
        this.finalData = msg.content;
        this.isLoading = false;
        this.status = 'Project generated successfully!';
        this.handsonAgent.close();
      } else if (msg.type === 'error') {
        this.error = msg.content;
        this.isLoading = false;
        this.status = 'An error occurred during generation.';
      }
    });
  }

  approve() {
    this.handsonAgent.sendFeedback('approve');
  }

  suggest() {
    const suggestions = prompt('Enter additional topics, comma-separated:');
    if (suggestions) {
      this.handsonAgent.sendFeedback('suggest', suggestions.split(',').map(s => s.trim()));
    }
  }

  /**
   * Regenerate SRS with current content
   */
  regenerateSrs() {
    if (this.srsReview && this.srsReview.content) {
      // Use 'suggest' with the current SRS content to trigger regeneration
      this.handsonAgent.sendFeedback('suggest', [this.srsReview.content]);
    }
  }

  /**
   * Handle SRS content changes from textarea
   */
  onSrsContentChange(event: any) {
    if (this.srsReview) {
      this.srsReview.content = event.target.value;
    }
  }

  /**
     * Get display text for tech stack (from query params or input)
     */
    getTechStackDisplay(): string {
        if (this.params.tech_stack && this.params.tech_stack.length > 0) {
            return this.params.tech_stack.map((stack: any) => stack.name || stack).join(', ');
        }
        return this.techStackName || '';
    }

    /**
     * Get display text for concepts (from query params or input)
     */
    getConceptsDisplay(): string {
         if (this.params.concepts && this.params.concepts.length > 0) {
             return this.params.concepts.map((concept: any) => concept.name || concept).join(', ');
         }
         return this.topicsInput || '';
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
     * Navigate to the next workflow step or save assessment
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
        // Unknown component, fallback to save assessment
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

  saveHandson() {
    if (this.finalData) {
      this.handsonAgent.storeHandson(this.finalData).subscribe(response => {
        let handsonId = response.handson_id;
        sessionStorage.setItem("handson_id", handsonId);
        this.handsonStored = true;
        
        // Proceed to next workflow step or save assessment
        this.goToNextWorkflowStep();
      }, err => {
        this.error = 'Failed to save HandsOn record.';
      });
    }
  }
}

