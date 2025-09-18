import { Component, OnInit } from '@angular/core';
import { HandsonAgentService, AgentMessage } from '../../services/hands-on.service';
import { FormsModule } from '@angular/forms';
import { Router, ActivatedRoute } from '@angular/router';
import { SharedDropdownComponent } from '../shared/shared-dropdown/shared-dropdown.component';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-handson-workflow',
  imports: [CommonModule, FormsModule, SharedDropdownComponent],
  templateUrl: './hands-on-gen.component.html'
})
export class HandsonWorkflowComponent implements OnInit {
  duration = 30;
  difficulty = 'intermediate';

  difficultyLevels = [
    { id: 'beginner', name: 'Beginner' },
    { id: 'intermediate', name: 'Intermediate' },
    { id: 'advanced', name: 'Advanced' }
  ];
  selectedDifficultyLevel: any = { id: 'intermediate', name: 'Intermediate' };

  readOnlyTechStack: string = '';
  readOnlyTopics: string[] = [];
  selectedTechStack: any = null;

  isLoading: boolean = false;

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

  onDifficultyChange(selected: any) {
    this.selectedDifficultyLevel = selected;
    this.difficulty = selected ? selected.id : 'intermediate';
  }

  srsReview?: AgentMessage;
  finalData?: any;
  error?: string;
  handsonStored: boolean = false;

  onSubmit() {
    this.isLoading = true;
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
    console.log(params);
    this.handsonAgent.connect(params).subscribe(msg => {
      this.isLoading = false;
      if (msg.type === 'srs_review') {
        this.srsReview = msg;
      } else if (msg.type === 'final') {
        this.finalData = msg.content;
        this.handsonAgent.close();
      } else if (msg.type === 'error') {
        this.error = msg.content;
      }
    }, err => {
      this.isLoading = false;
      this.error = 'Failed to start Hands-On.';
    });
  }

  approve() {
    this.isLoading = true;
    this.handsonAgent.sendFeedback('approve');
    // Simulate loader for feedback, reset after short delay
    console.log(this.readOnlyTechStack)
    setTimeout(() => { this.isLoading = false; }, 1000);
  }

  suggest() {
    const suggestions = prompt('Enter additional topics, comma-separated:');
    if (suggestions) {
      this.isLoading = true;
      this.handsonAgent.sendFeedback('suggest', suggestions.split(',').map(s => s.trim()));
      setTimeout(() => { this.isLoading = false; }, 1000);
    }
  }

  proceedToSaveAssessment() {
    this.isLoading = true;
    this.router.navigate(['/create-assessment'], {
      queryParams: { step: 'save' }
    });
    setTimeout(() => { this.isLoading = false; }, 1000);
  }

  saveHandson() {
    if (this.finalData) {
      this.isLoading = true;
      this.handsonAgent.storeHandson(this.finalData).subscribe(response => {
        let handsonId = response.handson_id;
        sessionStorage.setItem("handson_id", handsonId);
        this.handsonStored = true;
        this.isLoading = false;
        this.proceedToSaveAssessment();
      }, err => {
        this.isLoading = false;
        this.error = 'Failed to save HandsOn record.';
      });
    }
  }
}
