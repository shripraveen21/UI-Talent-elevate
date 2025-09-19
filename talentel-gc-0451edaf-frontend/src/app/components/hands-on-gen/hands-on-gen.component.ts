import { Component, OnInit } from '@angular/core';
import { HandsonAgentService, AgentMessage } from '../../services/hands-on.service';
import { FormsModule } from '@angular/forms';
import { Router, ActivatedRoute } from '@angular/router';
import { SharedDropdownComponent } from '../shared/shared-dropdown/shared-dropdown.component';
import { CommonModule } from '@angular/common';
import { MarkdownModule } from 'ngx-markdown';

@Component({
  selector: 'app-handson-workflow',
  imports: [CommonModule, FormsModule, SharedDropdownComponent, MarkdownModule],
  templateUrl: './hands-on-gen.component.html'
})
export class HandsonWorkflowComponent implements OnInit {
  // Configuration properties
  duration = 30;
  difficulty = 'intermediate';

  difficultyLevels = [
    { id: 'beginner', name: 'Beginner' },
    { id: 'intermediate', name: 'Intermediate' },
    { id: 'advanced', name: 'Advanced' }
  ];
  selectedDifficultyLevel: any = { id: 'intermediate', name: 'Intermediate' };

  // Read-only data from previous steps
  readOnlyTechStack: string = '';
  readOnlyTopics: string[] = [];
  selectedTechStack: any = null;

  // Individual loading states for better UX - mirroring debug component pattern
  isStarting: boolean = false;        // For Start Hands-On button
  isApproving: boolean = false;       // For Approve button
  isSuggesting: boolean = false;      // For Suggest Changes button
  isSaving: boolean = false;          // For Save HandsOn button
  
  // Legacy loading state for backward compatibility
  isLoading: boolean = false;

  // Status and error management - enhanced following debug component pattern
  status: string = '';
  error?: string;
  feedbackError: string | null = null;
  userFeedback: string = '';          // For human-in-the-loop feedback

  constructor(
    private handsonAgent: HandsonAgentService,
    private router: Router,
    private route: ActivatedRoute
  ) { }

  ngOnInit() {
    // Try to get techstack and topics from query params first
    this.route.queryParams.subscribe(params => {
      let techStackName = '';
      let topics: string[] = [];
      if (params['techStack']) {
        try {
          const techStackObj = JSON.parse(params['techStack']);
          techStackName = techStackObj.name || '';
          this.selectedTechStack = techStackObj;
        } catch (e) { }
      }
      if (params['concepts']) {
        try {
          const conceptsArr = JSON.parse(params['concepts']);
          topics = Array.isArray(conceptsArr) ? conceptsArr.map((c: any) => c.name) : [];
        } catch (e) { }
      }
      // If not found in query params, fallback to sessionStorage
      if (!techStackName || topics.length === 0) {
        const assessmentDetailsRaw = sessionStorage.getItem('assessmentDetails');
        if (assessmentDetailsRaw) {
          try {
            const details = JSON.parse(assessmentDetailsRaw);
            console.log(details)
            techStackName = details.selectedTechStack?.name || '';
            this.selectedTechStack = details.selectedTechStack || null;
            topics = Array.isArray(details.selectedConcepts)
              ? details.selectedConcepts.map((c: any) => c.name)
              : [];
          } catch (e) { }
        }
      }
      this.readOnlyTechStack = techStackName;
      this.readOnlyTopics = topics;
    });
  }

  /**
   * Handles difficulty level selection changes
   */
  onDifficultyChange(selected: any) {
    this.selectedDifficultyLevel = selected;
    this.difficulty = selected ? selected.id : 'intermediate';
  }

  // Component state properties
  srsReview?: AgentMessage;
  finalData?: any;
  handsonStored: boolean = false;

  /**
   * Initiates the hands-on project generation process
   * Enhanced with individual loading state management
   */
  onSubmit() {
    // Set individual loading state for start button only
    this.isStarting = true;
    this.isLoading = true; // Keep for backward compatibility
    this.status = 'Starting hands-on project generation...';
    this.error = undefined;
    this.feedbackError = null;

    const params = {
      tech_stack: [
        (this.selectedTechStack && this.selectedTechStack.name)
          ? this.selectedTechStack
          : { name: this.readOnlyTechStack }
      ],
      topics: this.readOnlyTopics,
      difficulty: this.difficulty,
      duration: this.duration
    };
    
    console.log('[HandsOn] Starting with params:', params);
    
    this.handsonAgent.connect(params).subscribe(msg => {
      // Reset loading states only for initial connection, not for approval processing
      if (msg.type === 'srs_review') {
        this.isStarting = false;
        this.isLoading = false;
        this.srsReview = msg;
        this.status = 'SRS generated successfully! Please review and provide feedback.';
      } else if (msg.type === 'final') {
        // Keep approval loading states active until save is complete
        this.finalData = msg.content;
        this.status = 'SRS finalized! Saving to database...';
        this.handsonAgent.close();
        
        // Automatically save to database without showing the final data step
        // Loading states will be reset in autoSaveHandson after successful save
        this.autoSaveHandson();
      } else if (msg.type === 'error') {
        // Reset all loading states on error
        this.isStarting = false;
        this.isApproving = false;
        this.isLoading = false;
        this.error = msg.content;
        this.status = 'Error occurred during generation. Please try again.';
        this.handsonAgent.close();
      }
    }, err => {
      // Reset all loading states on connection error
      this.isStarting = false;
      this.isApproving = false;
      this.isLoading = false;
      this.error = 'Failed to start Hands-On generation.';
      this.status = 'Connection error. Please check your network and try again.';
      this.feedbackError = 'Failed to connect to hands-on generation service';
      console.error('[HandsOn] Connection error:', err);
    });
  }

  /**
   * Approves the current SRS and proceeds to finalization
   * Enhanced with individual loading state management
   */
  approve() {
    // Set individual loading state for approve button only
    this.isApproving = true;
    this.isLoading = true; // Keep for backward compatibility
    this.status = 'Approving SRS and processing in background...';
    this.error = undefined;
    this.feedbackError = null;

    // Send approval feedback - the WebSocket handler will manage state updates
    this.handsonAgent.sendFeedback('approve');
    
    // Note: Loading states will be managed by the WebSocket message handler
    // when 'final' message is received, ensuring proper background processing
  }

  /**
   * Handle suggest changes with user feedback
   * @param feedback - Optional user feedback for suggestions
   */
  suggest(feedback?: string) {
    // Use provided feedback or prompt for input if none provided
    const suggestions = feedback || prompt('Enter additional topics, comma-separated:');
    if (suggestions) {
      // Set individual loading state for suggest button only
      this.isSuggesting = true;
      this.isLoading = true; // Keep for backward compatibility
      this.status = 'Sending suggestions...';
      this.error = undefined;
      this.feedbackError = null;

      // Handle both string feedback and comma-separated topics
      const suggestionArray = typeof suggestions === 'string' && suggestions.includes(',') 
        ? suggestions.split(',').map(s => s.trim())
        : [suggestions];

      this.handsonAgent.sendFeedback('suggest', suggestionArray);
      setTimeout(() => { 
        this.isSuggesting = false;
        this.isLoading = false;
        this.status = 'Suggestions sent successfully!';
        // Clear user feedback after successful submission
        this.userFeedback = '';
      }, 1000);
    }
  }

  /**
   * Navigates to save assessment page with current data
   */
  proceedToSaveAssessment() {
    this.isLoading = true;
    this.router.navigate(['/create-assessment'], {
      queryParams: { step: 'save' }
    });
    setTimeout(() => { this.isLoading = false; }, 1000);
  }

  /**
   * Automatically saves the hands-on project to the backend after approval
   * This method is called when finalData is received to skip the manual save step
   */
  autoSaveHandson() {
    if (this.finalData) {
      // Set loading state for auto-save process - keep approval loader active
      this.isSaving = true;
      this.isLoading = true;
      this.status = 'Saving hands-on project to database...';
      this.error = undefined;
      this.feedbackError = null;

      this.handsonAgent.storeHandson(this.finalData).subscribe(response => {
        let handsonId = response.handson_id;
        sessionStorage.setItem("handson_id", handsonId);
        this.handsonStored = true;
        
        // Reset all loading states only after successful save
        this.isSaving = false;
        this.isApproving = false;
        this.isLoading = false;
        this.status = 'Hands-on project saved successfully! Redirecting...';
        
        // Automatically proceed to save assessment after successful save
        setTimeout(() => {
          this.proceedToSaveAssessment();
        }, 1500); // Brief delay to show success message
      }, err => {
        // Reset all loading states on save error
        this.isSaving = false;
        this.isApproving = false;
        this.isLoading = false;
        this.error = 'Failed to save HandsOn record.';
        this.status = 'Error occurred while saving. Please try again.';
        this.feedbackError = 'Failed to save hands-on project to server';
        console.error('[HandsOn] Auto-save error:', err);
      });
    }
  }

  /**
   * Saves the hands-on project to the backend
   * Enhanced with individual loading state management
   */
  saveHandson() {
    if (this.finalData) {
      // Set individual loading state for save button only
      this.isSaving = true;
      this.isLoading = true; // Keep for backward compatibility
      this.status = 'Saving hands-on project...';
      this.error = undefined;
      this.feedbackError = null;

      this.handsonAgent.storeHandson(this.finalData).subscribe(response => {
        let handsonId = response.handson_id;
        sessionStorage.setItem("handson_id", handsonId);
        this.handsonStored = true;
        this.isSaving = false;
        this.isLoading = false;
        this.status = 'Hands-on project saved successfully!';
        this.proceedToSaveAssessment();
      }, err => {
        this.isSaving = false;
        this.isLoading = false;
        this.error = 'Failed to save HandsOn record.';
        this.status = 'Error occurred while saving. Please try again.';
        this.feedbackError = 'Failed to save hands-on project to server';
        console.error('[HandsOn] Save error:', err);
      });
    }
  }
}
