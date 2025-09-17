import { Component, Input, OnInit } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { CommonModule } from '@angular/common';
import { environment } from '../../../environments/environment';

@Component({
  selector: 'app-debug-feedback',
  templateUrl: './debug-feedback.component.html',
  imports: [CommonModule]
})
export class DebugFeedbackComponent implements OnInit {
  @Input() debugId!: number;
  @Input() userId!: number;
  feedbackData: any;
  loading = false;
  error: string | null = null;
  

  constructor(private http: HttpClient) {}

  ngOnInit() {
    this.fetchFeedback();
  }

  fetchFeedback() {
    this.loading = true;
    this.error = null;
    this.debugId=1 // Change for use
    this.userId=7 // Change for use
    this.http.get<any>(`${environment.apiUrl}/debug/${this.debugId}?user_id=${this.userId}`)
      .subscribe({
        next: (data) => {
          this.feedbackData = data;
          this.loading = false;
        },
        error: (err) => {
          this.error = err.error?.detail || 'Error fetching feedback';
          this.loading = false;
        }
      });
  }
}