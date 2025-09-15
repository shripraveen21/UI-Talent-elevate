import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router, ActivatedRoute } from '@angular/router';

import { McqAgentService } from '../../services/mcq-agent/mcq-agent.service';
import { TechStackAgentService } from '../../services/techstack-agent/techstack-agent.service';
import { TestListingService } from '../../services/test-listing/test-listing.service';
import { ToastService } from '../../services/toast/toast.service';

@Component({
  selector: 'app-create-assessment',
  imports: [CommonModule, FormsModule],
  templateUrl: './create-assessment.component.html',
  styleUrl: './create-assessment.component.css'
})
export class CreateAssessmentComponent implements OnInit {

  selectedComponents = {
    mcq: false,
    debug: false,
    handsOn: false
  };

  techStacks: any[] = [];
  topics: any[] = [];
  selectedTechStack: any = null;
  showTechStackDropdown: boolean = false;
  showTopicConceptDropdown = false;
  levels: ('beginner' | 'intermediate' | 'advanced')[] = ['beginner', 'intermediate', 'advanced'];
  selectedConcepts: any[] = []; // { name, level, topic_id }
  error: string = '';

  testName: string = '';
  testDescription: string = '';
  testDuration: number = 60;
  currentUserId: number = 1; // Replace with actual user ID from auth service

  quiz_id?: number;
  debug_id?: number;

  constructor(
    private router:Router,
    private route: ActivatedRoute,
    private mcqAgentService: McqAgentService,
    private techStackAgentService: TechStackAgentService,
    private testListingService: TestListingService,
    private toastService: ToastService
  ) {}

  ngOnInit(): void {
    // Restore test details and IDs from sessionStorage if present
    const savedDetails = sessionStorage.getItem('assessmentDetails');
    if (savedDetails) {
      const details = JSON.parse(savedDetails);
      this.selectedTechStack = details.selectedTechStack || null;
      this.selectedConcepts = details.selectedConcepts || [];
      this.testDescription = details.testDescription || '';
      this.testName = details.testName || '';
    }
    const quizId = sessionStorage.getItem('quiz_id');
    if (quizId) {
      this.quiz_id = Number(quizId);
    }
    const debugId = sessionStorage.getItem('exercise_id');
    if (debugId) {
      this.debug_id = Number(debugId);
    }
    this.loadTechStacks();

    // If a tech stack was restored, fetch its topics
    if (this.selectedTechStack) {
      this.fetchTopicsForSelectedTechStack();
    }

    // Check if we're returning from workflow to save assessment
    this.route.queryParams.subscribe(params => {
      if (params['step'] === 'save') {
        // Auto-trigger save assessment after a brief delay
        setTimeout(() => {
          this.saveAssessment();
        }, 500);
      }
    });
  }

  loadTechStacks() {
    this.techStackAgentService.getTechStacks().subscribe({
      next: (stacks: any[]) => {
        this.techStacks = stacks;
      },
      error: () => {
        this.techStacks = [];
      }
    });
  }

  fetchTopicsForSelectedTechStack() {
    if (!this.selectedTechStack) {
      this.topics = [];
      return;
    }
    // Use the tech stack's name to fetch topics
    const techStackName = this.selectedTechStack.name;
    this.techStackAgentService.getTopics(techStackName).subscribe({
      next: (topicsData: any[]) => {
        this.topics = topicsData.map((t: any) => ({
          name: t.name,
          level: t.difficulty,
          tech_stack_id: t.tech_stack_id,
          topic_id: t.topic_id
        }));
      },
      error: () => {
        this.topics = [];
        this.error = `Failed to fetch topics for ${techStackName}`;
      }
    });
  }

  availableConceptsByLevel(level: 'beginner' | 'intermediate' | 'advanced') {
    return this.topics.filter((c: any) => c.level === level);
  }

  isConceptSelected(concept: any) {
    return this.selectedConcepts.some(c => c.topic_id === concept.topic_id);
  }

  toggleConcept(concept: any, checked: boolean) {
    const idx = this.selectedConcepts.findIndex(c => c.topic_id === concept.topic_id);
    if (checked && idx === -1) {
      this.selectedConcepts.push({
        name: concept.name,
        level: concept.level,
        topic_id: concept.topic_id
      });
    } else if (!checked && idx > -1) {
      this.selectedConcepts.splice(idx, 1);
    }
    this.updateAssessmentDetailsStorage();
  }

  removeConcept(concept: any) {
    const idx = this.selectedConcepts.findIndex(c => c.topic_id === concept.topic_id);
    if (idx > -1) {
      this.selectedConcepts.splice(idx, 1);
      this.updateAssessmentDetailsStorage();
    }
  }

  toggleComponent(type: 'mcq' | 'debug' | 'handsOn') {
    this.selectedComponents[type] = !this.selectedComponents[type];
    this.updateAssessmentDetailsStorage();
  }

  goToMcqQuiz(event: Event) {
    event.stopPropagation();
    this.updateAssessmentDetailsStorage();
    // Store the workflow sequence in session storage
    this.storeWorkflowSequence();
    this.router.navigate(['/mcq-quiz'], {
      queryParams: {
        techStack: JSON.stringify({
          id: this.selectedTechStack?.id || this.selectedTechStack?.tech_stack_id,
          name: this.selectedTechStack?.name
        }),
        concepts: JSON.stringify(this.selectedConcepts)
      }
    });
  }

  goToDebugExercise(event: Event) {
    event.stopPropagation();
    this.updateAssessmentDetailsStorage();
    // Store the workflow sequence in session storage
    this.storeWorkflowSequence();
    this.router.navigate(['/debug-exercise'], {
      queryParams: {
        techStack: JSON.stringify({
          id: this.selectedTechStack?.id || this.selectedTechStack?.tech_stack_id,
          name: this.selectedTechStack?.name
        }),
        concepts: JSON.stringify(this.selectedConcepts)
      }
    });
  }

  onTechStackChange(event: Event) {
    const techStackId = Number((event.target as HTMLSelectElement).value);
    this.selectedTechStack = this.techStacks.find(
      stack => stack.id === techStackId || stack.tech_stack_id === techStackId
    );
    this.selectedConcepts = []; // Clear concepts when tech stack changes
    this.updateAssessmentDetailsStorage();
    this.fetchTopicsForSelectedTechStack(); // Fetch topics for the selected stack
  }

  selectTechStack(stack: any) {
    this.selectedTechStack = stack;
    this.showTechStackDropdown = false; // Auto-close after selection
    this.selectedConcepts = [];
    this.updateAssessmentDetailsStorage();
    this.fetchTopicsForSelectedTechStack();
  }

  onTechStackBlur(event: FocusEvent) {
    // Close dropdown when focus is lost, but allow time for click events to process
    setTimeout(() => {
      this.showTechStackDropdown = false;
    }, 150);
  }



  onConceptCheckboxChange(concept: any, event: Event) {
    const target = event.target as HTMLInputElement;
    this.toggleConcept(concept, target.checked);
  }

  // Select all concepts for a specific level
  selectAllConceptsForLevel(level: 'beginner' | 'intermediate' | 'advanced') {
    const conceptsForLevel = this.availableConceptsByLevel(level);
    
    // Add all concepts from this level that aren't already selected
    conceptsForLevel.forEach(concept => {
      if (!this.isConceptSelected(concept)) {
        this.selectedConcepts.push({
          name: concept.name,
          level: concept.level,
          topic_id: concept.topic_id
        });
      }
    });
    
    // Update storage after selecting all
    this.updateAssessmentDetailsStorage();
  }

  clearTechStack() {
    this.selectedTechStack = null;
    this.selectedConcepts = [];
    this.topics = [];
    this.updateAssessmentDetailsStorage();
  }

  onTestNameChange(name: string) {
    this.testName = name;
    this.updateAssessmentDetailsStorage();
  }

  onTestDescriptionChange(desc: string) {
    this.testDescription = desc;
    this.updateAssessmentDetailsStorage();
  }

  updateAssessmentDetailsStorage() {
    sessionStorage.setItem('assessmentDetails', JSON.stringify({
      selectedTechStack: this.selectedTechStack,
      selectedConcepts: this.selectedConcepts,
      testName: this.testName,
      testDescription: this.testDescription
    }));
  }

  storeWorkflowSequence() {
    const selectedComponentsList = [];
    if (this.selectedComponents.mcq) selectedComponentsList.push('mcq');
    if (this.selectedComponents.debug) selectedComponentsList.push('debug');
    if (this.selectedComponents.handsOn) selectedComponentsList.push('handsOn');
    
    sessionStorage.setItem('workflowSequence', JSON.stringify(selectedComponentsList));
    sessionStorage.setItem('currentWorkflowStep', '0');
  }

  startSequentialWorkflow() {
    if (!this.selectedTechStack || this.selectedConcepts.length === 0) {
      this.toastService.showError('Please select tech stack and concepts before starting the workflow.');
      return;
    }

    const selectedComponentsList = [];
    if (this.selectedComponents.mcq) selectedComponentsList.push('mcq');
    if (this.selectedComponents.debug) selectedComponentsList.push('debug');
    if (this.selectedComponents.handsOn) selectedComponentsList.push('handsOn');

    if (selectedComponentsList.length === 0) {
      this.toastService.showError('Please select at least one assessment component.');
      return;
    }

    this.updateAssessmentDetailsStorage();
    this.storeWorkflowSequence();

    // Start with the first component
    const firstComponent = selectedComponentsList[0];
    if (firstComponent === 'mcq') {
      this.router.navigate(['/mcq-quiz'], {
        queryParams: {
          techStack: JSON.stringify({
            id: this.selectedTechStack?.id || this.selectedTechStack?.tech_stack_id,
            name: this.selectedTechStack?.name
          }),
          concepts: JSON.stringify(this.selectedConcepts)
        }
      });
    } else if (firstComponent === 'debug') {
      this.router.navigate(['/debug-exercise'], {
        queryParams: {
          techStack: JSON.stringify({
            id: this.selectedTechStack?.id || this.selectedTechStack?.tech_stack_id,
            name: this.selectedTechStack?.name
          }),
          concepts: JSON.stringify(this.selectedConcepts)
        }
      });
    }
    // Add handsOn navigation when implemented
  }

  saveAssessment() {
    const quizId = sessionStorage.getItem('quiz_id');
    const debugId = sessionStorage.getItem('exercise_id');
    const payload: any = {
      test_name: this.testName,
      description: this.testDescription,
      duration: this.testDuration,
      created_by: this.currentUserId,
      quiz_id: quizId ? Number(quizId) : null,
      debug_test_id: debugId ? Number(debugId) : null,
      tech_stack: this.selectedTechStack,
      concepts: this.selectedConcepts
    };
    console.log('Test creation payload:', payload);
    Object.keys(payload).forEach(key => {
      console.log(`${key}:`, payload[key], 'type:', typeof payload[key]);
    });
    this.testListingService.createTest(payload).subscribe({
      next: (response) => {
        console.log('Assessment stored successfully:', response);
        this.toastService.showSuccess('Assessment created and stored successfully!');
        // Clean up session storage
        sessionStorage.removeItem('assessmentDetails');
        sessionStorage.removeItem('quiz_id');
        sessionStorage.removeItem('exercise_id');
        sessionStorage.removeItem('workflowSequence');
        sessionStorage.removeItem('currentWorkflowStep');
        // Navigate back to dashboard
        this.router.navigate(['/manager-dashboard']);
      },
      error: (err) => {
        console.error('Error storing assessment:', err);
        const errorMessage = err?.error?.message || 'Failed to store assessment';
        this.error = errorMessage;
        this.toastService.showError(errorMessage);
      }
    });
  }
}
