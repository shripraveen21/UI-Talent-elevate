import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';
import { HttpClient } from '@angular/common/http';

export interface SuggestionPayload {
  collaborator_id: number;
  capability_leader_id: number;
  tech_stack_id: number;
  message: string;
}

export interface SuggestionForLeader {
  id: number;
  collaborator_id: number;
  collaborator_name: string;
  tech_stack_id: number;
  tech_stack_name: string;
  message: string;
  raised_at: string; // ISO date string
}

@Injectable({
  providedIn: 'root'
})
export class YourSuggestionService {
  constructor(private http: HttpClient) {}

  raiseSuggestion(suggestion: SuggestionPayload): Observable<any> {
    return this.http.post(environment.apiUrl+'/suggestion', suggestion);
  }

  getSuggestionsForLeader(clId: number): Observable<SuggestionForLeader[]> {
    return this.http.get<SuggestionForLeader[]>(environment.apiUrl+`/suggestions/for-leader/${clId}`);
  }

  deleteSuggestion(suggestionId: number): Observable<any> {
    return this.http.delete(`${environment.apiUrl}/suggestion/${suggestionId}`);
  }
}
