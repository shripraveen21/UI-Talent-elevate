import { Component } from "@angular/core";
import { CommonModule } from "@angular/common";
import { FormsModule } from "@angular/forms";
import { environment } from "../../../environments/environment";
import { HttpClient } from "@angular/common/http";

@Component({
  selector: 'app-topics-request',
  standalone: true,
  imports: [CommonModule, FormsModule],
  styleUrls: ['./topics-request.component.css'],
  templateUrl: './topics-request.component.html'
})
export class TopicRequest {
  baseUrl = environment.apiUrl;
  techStack = '';
  details = '';

  constructor(public http: HttpClient) {}

  onSubmit() {
    const payload = {
      name: this.techStack,
      description: this.details
    };
    this.http.post(`${this.baseUrl}/request/techstack`, payload)
      .subscribe({
        next: (response) => {
          // Handle success (show a message or reset form)
          console.log('Request submitted:', response);
        },
        error: (err) => {
          // Handle error (show error message)
          console.error('Submission error:', err);
        }
      });
  }
}