import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment';

export interface TechStack {
  tech_stack_id: number;
  name: string;
}

@Injectable({
  providedIn: 'root'
})
export class SkillUpgradeService {
  private baseUrl = environment.apiUrl; 

  constructor(private http: HttpClient) {}

  getUserTechStacks(token: string): Observable<TechStack[]> {
    const headers = new HttpHeaders().set('Authorization', `Bearer ${token}`);
    return this.http.get<TechStack[]>(`${this.baseUrl}/get-skills`, { headers });
  }

  createSkillUpgradeTest(token: string, techStack: string, level: string): Observable<any> {
    const headers = new HttpHeaders().set('Authorization', `Bearer ${token}`);
    const payload = { tech_stack: techStack, level: level };
    return this.http.post(`${this.baseUrl}/skill-upgrade`, payload, { headers });
  }

  completeSkillUpgrade(token: string, testId: number): Observable<any> {
    const headers = new HttpHeaders().set('Authorization', `Bearer ${token}`);
    // Backend expects test_id as query param, not in body
    return this.http.post(`${this.baseUrl}/skill-upgrade/complete?test_id=${testId}`, null, { headers });
  }
}
