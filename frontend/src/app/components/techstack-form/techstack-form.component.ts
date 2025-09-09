import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { TechStackAgentService, TechStackParams, Topic, AgentMessage } from '../../services/techstack-agent/techstack-agent.service';

type Level = 'beginner' | 'intermediate' | 'advanced';

@Component({
  selector: 'app-techstack-form',
  templateUrl: './techstack-form.component.html',
  styleUrls: ['./techstack-form.component.css'],
  standalone: true,
  imports: [CommonModule, FormsModule]
})
export class TechStackFormComponent {
  params: TechStackParams = {
    name: '',
  };

  topics: Topic[] = [];
  log: string[] = [];
  reviewIteration = 0;
  wsConnected = false;
  showControls = false;

  constructor(private agent: TechStackAgentService) {}

  connect() {
    this.log = [];
    this.topics = [];
    this.wsConnected = true;
    this.agent.connect(this.params).subscribe((msg: AgentMessage) => {
      this.log.push(JSON.stringify(msg, null, 2));
      if (msg.type === 'review') {
        this.topics = msg.content;
        this.reviewIteration = msg.iteration || 1;
        this.showControls = true;
      } else if (msg.type === 'final') {
        if (msg.content.topics) {
          this.topics = msg.content.topics;
        } else {
          this.topics = msg.content;
        }
        this.showControls = false;
        // Show a success message or update UI here
        this.log.push('Tech stack and topics saved successfully!');
      } else if (msg.type === 'error') {
        this.showControls = false;
      }
    });
  }

  sendDecision(decision: string, feedback?: string) {
    this.agent.sendDecision(decision, feedback);
    this.log.push(`Sent decision: ${decision}${feedback ? ' with feedback: ' + feedback : ''}`);
  }

  closeWs() {
    this.agent.close();
    this.wsConnected = false;
    this.showControls = false;
  }

  get formattedTopicsJson(): string {
    const grouped: { [key: string]: string[] } = {
      beginner: [],
      intermediate: [],
      advanced: []
    };
    for (const topic of this.topics) {
      const level = (topic.level || '').toLowerCase();
      if (grouped[level]) {
        grouped[level].push(topic.name);
      }
    }
    return JSON.stringify(grouped, null, 2);
  }
}