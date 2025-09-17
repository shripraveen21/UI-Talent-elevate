import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';


@Injectable({ providedIn: 'root' })
export class CollaboratorService {
  private baseUrl = environment.apiUrl;

  constructor(private http: HttpClient) {}

  getCollaborators(): Observable<any[]> {
    return this.http.get<any[]>(`${this.baseUrl}/get-collaborators`);
  }

  upsertCollaborator(data: any): Observable<any> {
    return this.http.post<any>(`${this.baseUrl}/upsert-collaborator`, data);
  }

  deleteCollaborator(email: string): Observable<any> {
    return this.http.delete<any>(`${this.baseUrl}/delete-collaborator`, {
      params: { collaborator_email: email }
    });
  }
}