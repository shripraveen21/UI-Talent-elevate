import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Observable, throwError } from 'rxjs';
import { catchError } from 'rxjs/operators';

@Injectable({
  providedIn: 'root'
})
export class DashboardService {
  private apiUrl = 'http://localhost:8000'; // Update if needed

  constructor(private http: HttpClient) {}

  getAssignedTests(token: string): Observable<any[]> {
    const headers = new HttpHeaders().set('Authorization', `Bearer ${token}`);
    return this.http.get<any[]>(`${this.apiUrl}/employee-dashboard/assigned-tests`, { headers })
      .pipe(
        catchError((error) => {
          return throwError(() => error);
        })
      );
  }
  getTestDetails(testId: number, token: string): Observable<any> {
    const headers = new HttpHeaders().set('Authorization', `Bearer ${token}`);
    return this.http.get<any>(`${this.apiUrl}/employee-dashboard/start-test/${testId}`, { headers });
  }

  submitTestAnswers(testId: number, answers: any, token: string): Observable<any> {
    const headers = new HttpHeaders().set('Authorization', `Bearer ${token}`);
    // Backend expects: { test_id, answers, start_time }
    const payload = {
      test_id: testId,
      answers: answers.answers ? answers.answers : answers,
      start_time: answers.start_time ? answers.start_time : null
    };
    return this.http.post<any>(`${this.apiUrl}/employee-dashboard/submit-test`, payload, { headers });
  }

  getTestResults(testId: number, token: string): Observable<any> {
    const headers = new HttpHeaders().set('Authorization', `Bearer ${token}`);
    return this.http.get<any>(`${this.apiUrl}/employee-dashboard/score/${testId}`, { headers });
  }

  getTestFeedback(resultId: number, token: string): Observable<any> {
    const headers = new HttpHeaders().set('Authorization', `Bearer ${token}`);
    return this.http.get<any>(`${this.apiUrl}/employee-dashboard/feedback/${resultId}`, { headers });
  }
}
