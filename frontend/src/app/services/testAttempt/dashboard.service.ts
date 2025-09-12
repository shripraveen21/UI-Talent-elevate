import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Observable, throwError } from 'rxjs';
import { catchError } from 'rxjs/operators';
import { environment } from '../../../environments/environment';

@Injectable({
  providedIn: 'root'
})
export class DashboardService {
  private apiUrl = environment.apiUrl; // Update if needed

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

  getDebugTestDetails(debugTestId: number, token: string): Observable<any> {
    const headers = new HttpHeaders().set('Authorization', `Bearer ${token}`);
    return this.http.get<any>(`${this.apiUrl}/debug-test/start/${debugTestId}`, { headers });
  }

  submitDebugAnswers(debugTestId: number, answers: any, token: string): Observable<any> {
    const headers = new HttpHeaders().set('Authorization', `Bearer ${token}`);
    const payload = {
      debug_test_id: debugTestId,
      answers: answers.answers ? answers.answers : answers,
      start_time: answers.start_time ? answers.start_time : null
    };
    return this.http.post<any>(`${this.apiUrl}/debug-test/submit`, payload, { headers });
  }

  getDebugResults(debugTestId: number, token: string): Observable<any> {
    const headers = new HttpHeaders().set('Authorization', `Bearer ${token}`);
    return this.http.get<any>(`${this.apiUrl}/debug-test/score/${debugTestId}`, { headers });
  }
}
