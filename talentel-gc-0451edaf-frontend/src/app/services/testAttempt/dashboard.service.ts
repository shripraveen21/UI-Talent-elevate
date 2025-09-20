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

  getHandsonResult(handsonId: number, token: string): Observable<any> {
    const headers = new HttpHeaders().set('Authorization', `Bearer ${token}`);
    return this.http.get<any>(`${this.apiUrl}/handson-result/${handsonId}`, { headers });
  }

  evaluateDebugTest(debugId: number | string): Observable<any> {
    const token = localStorage.getItem('token') || '';
    const headers = new HttpHeaders().set('Authorization', `Bearer ${token}`);
    console.log(JSON.stringify({
      level: 'INFO',
      message: 'Submitting debug test for evaluation',
      debugId,
      timestamp: new Date().toISOString()
    }));
    return this.http.post<any>(`${this.apiUrl}/evaluate/debug/${debugId}`, {}, { headers }).pipe(
      catchError((error) => {
        console.error(JSON.stringify({
          level: 'ERROR',
          message: 'Error submitting debug test for evaluation',
          debugId,
          error: error?.message || error,
          timestamp: new Date().toISOString()
        }));
        return throwError(() => error);
      })
    );
  }


  evaluateHandsonTest(handsonId: number | string): Observable<any> {
    const token = localStorage.getItem('token') || '';
    const headers = new HttpHeaders().set('Authorization', `Bearer ${token}`);
    console.log(JSON.stringify({
      level: 'INFO',
      message: 'Submitting handson test for evaluation',
      handsonId,
      timestamp: new Date().toISOString()
    }));
    return this.http.post<any>(`${this.apiUrl}/evaluate/handson/${handsonId}`, {}, { headers }).pipe(
      catchError((error) => {
        console.error(JSON.stringify({
          level: 'ERROR',
          message: 'Error submitting handson test for evaluation',
          handsonId,
          error: error?.message || error,
          timestamp: new Date().toISOString()
        }));
        return throwError(() => error);
      })
    );
  }
}
