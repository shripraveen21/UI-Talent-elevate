import { Component, Output, EventEmitter,OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { QuizParams } from '../../services/mcq-agent/mcq-agent.service';
import { TechStackAgentService } from '../../services/techstack-agent/techstack-agent.service';


export interface TechStack {
  id: number;
  name: string;
  created_by: number;
  created_at: string; // ISO date string, e.g., "2025-09-08T20:17:57.363997"
}

export interface Topic {
  name: string;
  difficulty: 'beginner' | 'intermediate' | 'advanced';
  tech_stack_id: number;
  topic_id: number;
}

@Component({
  selector: 'app-mcq-form',
  templateUrl: './mcq-form.component.html',
  styleUrls: ['./mcq-form.component.css'],
  standalone: true,
  imports: [CommonModule, FormsModule]
})
export class McqFormComponent implements OnInit {
  public showTechStackDropdown = false;
  public showConceptDropdown = false;
  public techStacks: TechStack[] = [];
  public topics: Topic[] = [];
  public error: string = '';

  ngOnInit() {
    // Fetch tech stacks on component initialization
    this.techStackAgentService.getTechStacks().subscribe({
      next: (stacks: TechStack[]) => {
        this.techStacks = stacks;
        this.fetchAllTopics();
      },
      error: () => {
        this.error = 'Failed to fetch tech stacks';
      }
    });
  }

  // For dropdown levels
  public levels: ('beginner' | 'intermediate' | 'advanced')[] = ['beginner', 'intermediate', 'advanced'];

  // techStackOptions for dropdown
  public get techStackOptions(): TechStack[] {
    return this.techStacks;
  }

  // params: use concepts and topics for compatibility with QuizParams and template
  public params: QuizParams & { concepts: any[] } = {
    tech_stack: [],
    concepts: [],
    topics: [],
    num_questions: 5,
    duration: 15
  };

  @Output() submitParams = new EventEmitter<QuizParams>();

  constructor(public techStackAgentService: TechStackAgentService) { }

  public fetchAllTopics() {
    this.topics = [];
    this.techStacks.forEach(stack => {
      this.techStackAgentService.getTopics(stack.name).subscribe({
        next: (topicsData: Topic[]) => {
          // Normalize topic objects to have the correct structure
          const normalizedTopics = topicsData.map((t: any) => ({
            name: t.name,
            difficulty: t.difficulty,
            tech_stack_id: t.tech_stack_id,
            topic_id: t.topic_id
          }));
          this.topics = this.topics.concat(normalizedTopics);
          // Optionally update available concepts if needed
          // this.availableConcepts = this.topics;
          console.log("all topics got", this.topics);
        },
        error: () => {
          this.error = `Failed to fetch topics for ${stack.name}`;
        }
      });
    });
  }

  public toggleTechStack(stack: { id: number; name: string }) {
    const stackObj = this.techStacks.find(s => s.id === stack.id);
    if (!stackObj) return;
    const idx = this.params.tech_stack.findIndex(s => s.id === stackObj.id);
    if (idx === -1) {
      this.params.tech_stack = [...this.params.tech_stack, { id: stackObj.id, name: stackObj.name }];
    } else {
      this.params.tech_stack = this.params.tech_stack.filter(s => s.id !== stackObj.id);

      // Remove concepts that belong to the removed tech stack
      const validTopicIds = this.topics
        .filter(t => this.params.tech_stack.some(ts => ts.id === t.tech_stack_id))
        .map(t => t.topic_id);
      this.params.concepts = this.params.concepts.filter(
        (c: { topic_id: number }) => validTopicIds.includes(c.topic_id)
      );
    }
  }

  public removeTechStack(stack: { id: number; name: string }) {
    this.toggleTechStack(stack);
  }

  // Concept selection logic for template compatibility
  public removeConcept(concept: { name: string; topic_id: number }) {
    const idx = this.params.concepts.findIndex(
      c => c.topic_id === concept.topic_id
    );
    if (idx > -1) {
      this.params.concepts.splice(idx, 1);
    }
  }

  public toggleConcept(
    concept: Topic,
    checked: boolean
  ) {
    const idx = this.params.concepts.findIndex(
      c => c.topic_id === concept.topic_id
    );
    if (checked && idx === -1) {
      this.params.concepts.push({
        name: concept.name,
        level: concept.difficulty,
        topic_id: concept.topic_id
      });
    } else if (!checked && idx > -1) {
      this.params.concepts.splice(idx, 1);
    }
    // For debugging
    console.log("trying to print data ", this.params, "hei");
  }

  public isConceptSelected(concept: Topic) {
    return this.params.concepts.some(
      c => c.topic_id === concept.topic_id
    );
  }

  public availableConceptsByLevel(level: 'beginner' | 'intermediate' | 'advanced') {
    return this.topics.filter((c: Topic) => c.difficulty === level);
  }

  public onSubmit() {
    // Remove concepts property before emitting if QuizParams doesn't expect it
    const { concepts, ...paramsWithoutConcepts } = this.params;
    this.submitParams.emit({ ...paramsWithoutConcepts, topics: concepts });
  }

  public isTechStackSelected(stack: TechStack): boolean {
    return this.params.tech_stack.some(ts => ts.id === stack.id);
  }
}
