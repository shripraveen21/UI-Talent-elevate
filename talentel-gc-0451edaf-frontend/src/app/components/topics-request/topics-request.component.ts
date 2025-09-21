import { Component } from "@angular/core";
import { CommonModule } from "@angular/common";
import { FormsModule } from "@angular/forms";
import { Router } from "@angular/router";
import { environment } from "../../../environments/environment";
import { HttpClient } from "@angular/common/http";
import { BackButtonComponent } from '../shared/backbutton/backbutton.component';

@Component({
  selector: 'app-topics-request',
  standalone: true,
  imports: [CommonModule, FormsModule, BackButtonComponent],
  styleUrls: ['./topics-request.component.css'],
  templateUrl: './topics-request.component.html'
})
export class TopicRequest {
  baseUrl = environment.apiUrl;
  techStack = '';
  details = '';
  
  // UI State
  isLoading = false;
  showSuccess = false;
  showError = false;
  errorMessage = '';
  submitted = false;

  constructor(public http: HttpClient, private router: Router) {}

  onSubmit() {
    this.submitted = true;
    
    // Validation
    if (!this.techStack.trim() || !this.details.trim()) {
      this.showError = true;
      this.errorMessage = 'Please fill in all required fields.';
      this.hideMessages();
      return;
    }

    // Clear previous messages
    this.showSuccess = false;
    this.showError = false;
    this.isLoading = true;

    const payload = {
      name: this.techStack.trim(),
      description: this.details.trim()
    };
    
    this.http.post(`${this.baseUrl}/request/techstack`, payload)
      .subscribe({
        next: (response) => {
          this.isLoading = false;
          this.showSuccess = true;
          this.resetForm();
          this.hideMessages();
          console.log('Request submitted:', response);
        },
        error: (err) => {
          this.isLoading = false;
          this.showError = true;
          this.errorMessage = err.error?.message || 'An error occurred while submitting your request. Please try again.';
          this.hideMessages();
          console.error('Submission error:', err);
        }
      });
  }

  private resetForm() {
    this.techStack = '';
    this.details = '';
    this.submitted = false;
  }

  private hideMessages() {
    setTimeout(() => {
      this.showSuccess = false;
      this.showError = false;
    }, 5000);
  }

  returnToSkillUpgrade(): void {
    this.router.navigate(['/skill-upgrade']);
  }
}