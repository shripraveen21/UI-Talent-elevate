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

  createSkillUpgradeTest(token: string, techStack: string): Observable<any> {
    const headers = new HttpHeaders().set('Authorization', `Bearer ${token}`);
    return this.http.post(`${this.baseUrl}/skill-upgrade?tech_stack=${techStack}`, {}, { headers });
  }
}