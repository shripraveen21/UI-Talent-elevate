import { Component, OnInit } from '@angular/core';
import { FormBuilder, FormGroup, Validators, ReactiveFormsModule, FormsModule } from '@angular/forms';
import { CommonModule } from '@angular/common';
import { ActivatedRoute } from '@angular/router';
import { DebugExerciseAgentService } from '../../services/debug-exercise-agent/debug-exercise-agent.service';
import { TechStackAgentService } from '../../services/techstack-agent/techstack-agent.service';
import { ToastService } from '../../services/toast/toast.service';

@Component({
  selector: 'app-debug-exercise-form',
  templateUrl: './debug-exercise-form.component.html',
  styleUrls: ['./debug-exercise-form.component.css'],
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, FormsModule]
})
export class DebugExerciseFormComponent implements OnInit {
  debugForm: FormGroup;
  loading = false;
  error: string | null = null;
  data: any = null;
  iteration: number = 0;

  // Dropdown state
  showTechStackDropdown = false;
  showConceptDropdown = false;

  // Tech stack options fetched from DB
  techStackOptions: { id: number; name: string }[] = [];

  // Concepts mapped by tech stack, each with level, fetched from DB
  conceptOptions: Record<string, { name: string; level: 'beginner' | 'intermediate' | 'advanced' }[]> = {};

  levels: ('beginner' | 'intermediate' | 'advanced')[] = ['beginner', 'intermediate', 'advanced'];

  // Selected values
  tech_stack: string[] = [];
  concepts: { name: string; level: 'beginner' | 'intermediate' | 'advanced' }[] = [];

  // Split-screen functionality
  currentExerciseIndex = 0;
  userCode = '';
  codeOutput = '';

  constructor(
    private fb: FormBuilder,
    private debugService: DebugExerciseAgentService,
    private techStackAgentService: TechStackAgentService,
    private route: ActivatedRoute,
    private toastService: ToastService
  ) {
    this.debugForm = this.fb.group({
      tech_stack: [[], [Validators.required, this.arrayNotEmptyValidator]],
      concepts: [[], [Validators.required, this.arrayNotEmptyValidator]],
      num_questions: [1, [Validators.required, Validators.min(1)]],
      duration: [15, [Validators.required, Validators.min(1)]],
      difficulty: ['medium']
    });
  }

  // Custom validator to check if array is not empty
  arrayNotEmptyValidator(control: any) {
    const value = control.value;
    return (value && Array.isArray(value) && value.length > 0) ? null : { arrayEmpty: true };
  }

  ngOnInit() {
    // Fetch tech stack options from backend using injected service
    this.techStackAgentService.getTechStacks().subscribe({
      next: (options: any[]) => {
        this.techStackOptions = options;
        console.log('Tech stack options loaded:', this.techStackOptions);
      },
      error: (err: any) => {
        console.error('Failed to load tech stack options:', err);
        this.techStackOptions = [];
      }
    });

    this.route.queryParams.subscribe((params: Record<string, any>) => {
      if (params['techStack']) {
        try {
          // Try to parse as JSON first (new format)
          const techStackData = JSON.parse(params['techStack']);
          this.tech_stack = [techStackData.name || 'Selected Tech Stack'];
          this.debugForm.patchValue({ tech_stack: this.tech_stack });
        } catch {
          // Fallback for old format (just name)
          this.tech_stack = [params['techStack']];
          this.debugForm.patchValue({ tech_stack: this.tech_stack });
        }
      }
      if (params['concepts']) {
        try {
          this.concepts = JSON.parse(params['concepts']);
          this.debugForm.patchValue({ concepts: this.concepts });
        } catch {
          this.concepts = [];
        }
      }
    });
  }

  // Fetch concepts for selected tech stacks from DB
  fetchConceptsForSelectedStacks() {
    this.conceptOptions = {};
    this.tech_stack.forEach(stackName => {
      this.debugService.getConcepts(stackName).subscribe({
        next: (concepts: any[]) => {
          console.log('Concepts fetched for', stackName, concepts);
          this.conceptOptions[stackName] = concepts.map((c: any) => ({
            name: c.name,
            level: c.difficulty || c.level, // support both keys
            topic_id: c.topic_id // ensure topic_id is present for backend
          }));
        },
        error: (err) => {
          console.error('Error fetching concepts for', stackName, err);
          this.error = `Failed to fetch concepts for ${stackName}`;
        }
      });
    });
  }

  // Get concepts for selected tech stacks
  get availableConcepts(): { name: string; level: 'beginner' | 'intermediate' | 'advanced' }[] {
    const stacks = this.tech_stack;
    const concepts: { name: string; level: 'beginner' | 'intermediate' | 'advanced' }[] = [];
    stacks.forEach(stack => {
      if (this.conceptOptions[stack]) {
        concepts.push(...this.conceptOptions[stack]);
      }
    });
    // Remove duplicates by name+level
    return concepts.filter((c, i, arr) =>
      arr.findIndex(x => x.name === c.name && x.level === c.level) === i
    );
  }

  // Toggle tech stack selection
  toggleTechStack(stack: string) {
    const idx = this.tech_stack.indexOf(stack);
    if (idx === -1) {
      this.tech_stack = [...this.tech_stack, stack];
    } else {
      this.tech_stack = this.tech_stack.filter(s => s !== stack);
      // Remove concepts not in any selected stack
      const validConcepts = this.availableConcepts.map(c => c.name + c.level);
      this.concepts = this.concepts.filter(
        c => validConcepts.includes(c.name + c.level)
      );
    }
    this.debugForm.patchValue({ tech_stack: this.tech_stack, concepts: this.concepts });
    // Fetch concepts for selected stacks from DB
    this.fetchConceptsForSelectedStacks();
  }

  // Remove tech stack (for tag close button)
  removeTechStack(stack: string) {
    this.toggleTechStack(stack);
  }

  // Remove concept (for tag close button)
  removeConcept(concept: { name: string; level: 'beginner' | 'intermediate' | 'advanced' }) {
    const idx = this.concepts.findIndex(
      c => c.name === concept.name && c.level === concept.level
    );
    if (idx > -1) {
      this.concepts.splice(idx, 1);
      this.debugForm.patchValue({ concepts: this.concepts });
    }
  }

  // Toggle concept selection
  toggleConcept(concept: { name: string; level: 'beginner' | 'intermediate' | 'advanced' }, checked: boolean) {
    const idx = this.concepts.findIndex(
      c => c.name === concept.name && c.level === concept.level
    );
    if (checked && idx === -1) {
      this.concepts.push(concept);
    } else if (!checked && idx > -1) {
      this.concepts.splice(idx, 1);
    }
    this.debugForm.patchValue({ concepts: this.concepts });
  }

  // Check if concept is selected
  isConceptSelected(concept: { name: string; level: 'beginner' | 'intermediate' | 'advanced' }) {
    return this.concepts.some(
      c => c.name === concept.name && c.level === concept.level
    );
  }

  // Get available concepts by level for template
  availableConceptsByLevel(level: 'beginner' | 'intermediate' | 'advanced') {
    return this.availableConcepts.filter(c => c.level === level);
  }

  private parseExercises(agentResponse: any): any[] {
    if (
      agentResponse &&
      agentResponse.exercises &&
      Array.isArray(agentResponse.exercises.exercises)
    ) {
      return agentResponse.exercises.exercises;
    }
    if (
      agentResponse &&
      Array.isArray(agentResponse.exercises)
    ) {
      return agentResponse.exercises;
    }
    if (Array.isArray(agentResponse)) {
      return agentResponse;
    }
    return [];
  }

  startDebugExercise() {
    this.loading = true;
    this.error = null;
    this.data = null;
    const formValue = this.debugForm.value;
    const concepts_as_list = formValue.concepts.map((concept: { name: any; }) => concept.name);
    const payload = {
      tech_stack: formValue.tech_stack,
      concepts: concepts_as_list,
      num_questions: formValue.num_questions,
      duration: formValue.duration,
      difficulty: formValue.difficulty
    };
    this.debugService.startDebugExercise(payload).subscribe({
      next: (msg) => {
        if (msg.type === 'review' || msg.type === 'final') {
          this.data = this.parseExercises(msg.content);
          this.iteration = msg.iteration ?? 1;
          this.loading = false;
        } else if (msg.type === 'error') {
          this.error = msg.content;
          this.loading = false;
        }
      },
      error: (err) => {
        this.error = err.message || 'Error receiving exercises';
        this.loading = false;
      }
    });
  }

  sendDecision(decision: string, feedback: string = '') {

    this.loading = true;
    this.debugService.sendDecision(decision, feedback);
    if(decision == "APPROVE") {
      this.storeFinalExercise()
    }
    // Do not start a new WebSocket connection; rely on the existing subscription for updates.
  }

  async storeFinalExercise() {
    if (!this.data) return;
    try {
      this.loading = true;

      // Build payload for backend
      const formValue = this.debugForm.value;
      // tech_stack_id: extract ID(s) from techStackOptions
      console.log('techStackOptions:', this.techStackOptions);
      console.log('selected tech_stack:', formValue.tech_stack);
      let techStackId: number | null = null;
      console.log('techStackOptions before mapping:', this.techStackOptions);
      console.log('Selected tech_stack value:', formValue.tech_stack);
      if (!this.techStackOptions || this.techStackOptions.length === 0) {
        this.error = "Tech stack options not loaded. Please wait and try again.";
        this.loading = false;
        return;
      }
      if (Array.isArray(formValue.tech_stack) && formValue.tech_stack.length > 0) {
        const stackValue = formValue.tech_stack[0];
        let stackObj = null;
        // Try to match by ID if value is a number or numeric string
        if (!isNaN(Number(stackValue))) {
          stackObj = this.techStackOptions.find(s => String(s.id) === String(stackValue));
        }
        // If not found by ID, try by name
        if (!stackObj) {
          stackObj = this.techStackOptions.find(s => s.name === stackValue);
        }
        if (stackObj) {
          techStackId = stackObj.id;
        } else {
          this.error = `Selected tech stack "${stackValue}" not found in options.`;
          this.loading = false;
          return;
        }
      } else {
        this.error = "No tech stack selected.";
        this.loading = false;
        return;
      }

      // topic_ids: from selected concepts (ensure topic_id exists)
      const topicIds = Array.isArray(formValue.concepts)
        ? formValue.concepts.map((concept: any) => concept.topic_id).filter((id: any) => id !== undefined && id !== null)
        : [];

      // exercises: from this.data
      let exercisesPayload;
      if (this.data.exercises && this.data.metadata) {
        exercisesPayload = {
          exercises: this.data.exercises,
          metadata: this.data.metadata
        };
      } else {
        exercisesPayload = {
          exercises: Array.isArray(this.data) ? this.data : [],
          metadata: {}
        };
      }

      // Final payload for backend
      const payload = {
        tech_stack_id: techStackId,
        topic_ids: topicIds,
        num_questions: Number(formValue.num_questions ?? this.debugForm.get('num_questions')?.value),
        duration: Number(formValue.duration ?? this.debugForm.get('duration')?.value),
        exercises: exercisesPayload
      };

      const res = await this.debugService.storeDebugExercise(payload, "");
      // Save debug_id to localStorage if returned
      console.log(res);
      if (res && res.exercise_id) {
        sessionStorage.setItem('exercise_id', String(res.exercise_id));
      }
      this.toastService.showDebugExerciseCreated();
      this.loading = false;
    } catch (err: any) {
      const errorMessage = err.message || 'Failed to store debug exercise';
      this.error = errorMessage;
      this.toastService.showError(errorMessage);
      this.loading = false;
    }
  }

  // Split-screen functionality methods
  nextExercise() {
    if (this.currentExerciseIndex < this.data.length - 1) {
      this.currentExerciseIndex++;
      this.userCode = ''; // Reset code when switching exercises
      this.codeOutput = '';
    }
  }

  previousExercise() {
    if (this.currentExerciseIndex > 0) {
      this.currentExerciseIndex--;
      this.userCode = ''; // Reset code when switching exercises
      this.codeOutput = '';
    }
  }

  copyToEditor(code: string) {
    this.userCode = code;
  }

  runCode() {
    if (!this.userCode.trim()) {
      this.codeOutput = 'Error: No code to execute';
      return;
    }
    
    // Simulate code execution (replace with actual execution logic)
    this.codeOutput = `Executing code...\n\n${this.userCode}\n\n✓ Code executed successfully!\nOutput: [Simulated execution result]`;
  }

  resetCode() {
    this.userCode = '';
    this.codeOutput = '';
  }

  clearOutput() {
    this.codeOutput = '';
  }

  getLineCount(): number {
    return this.userCode ? this.userCode.split('\n').length : 0;
  }

  /**
   * Checks if the provided data is a non-empty array of objects (exercises).
   * Used to determine if agent data should be parsed or shown raw.
   */
  public isExerciseList(data: any): boolean {
    return Array.isArray(data) && data.length > 0 && typeof data[0] === 'object';
  }
}
