import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { map, Observable } from 'rxjs';
import { environment } from '../../../environments/environment';

@Injectable({
  providedIn: 'root'
})
export class TestListingService {
  private apiUrl = environment.apiUrl + '/tests/';

  constructor(private http: HttpClient) {}

  getTests(params: any = {}): Observable<any> {
    return this.http.get<any>(this.apiUrl, { params });
  }

  createTest(testData: any): Observable<any> {
    return this.http.post<any>(this.apiUrl, testData);
  }

  assignTest(assignData: any): Observable<any> {
    return this.http.post<any>(`${this.apiUrl}assign-test`, assignData);
  }

  getAssessments(): Observable<any[]> {
    // Use this.apiUrl for consistency
    return this.http.get<{ total: number, tests: any[] }>(this.apiUrl).pipe(
      map(response => response.tests)
    );
  }

  getAssessmentsCount(): Observable<number> {
    // Use this.apiUrl for consistency
    return this.http.get<{ total: number, tests: any[] }>(this.apiUrl).pipe(
      map(response => response.total)
    );
  }

  // Get employees who attempted a test and their scores
  getTestAttempts(testId: number): Observable<any> {
    return this.http.get<any>(`${this.apiUrl}${testId}/attempts`);
  }

  // Get tests created by the current user
  getTestsCreatedBySelf(): Observable<any> {
    return this.http.get<any>(`${this.apiUrl}createdBySelf`);
  }

  // Get submission status for quiz, debug, and handson for a test
  getTestSubmitStatus(testId: number): Observable<{quiz_isSubmitted: boolean, debug_isSubmitted: boolean, handson_isSubmitted: boolean}> {
    const url = environment.apiUrl + '/employee-dashboard/test-submit-status/' + testId;
    return this.http.get<{quiz_isSubmitted: boolean, debug_isSubmitted: boolean, handson_isSubmitted: boolean}>(url);
  }
}
