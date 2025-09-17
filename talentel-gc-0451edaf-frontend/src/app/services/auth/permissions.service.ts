import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';

@Injectable({ providedIn: 'root' })
export class PermissionsService {
  private baseUrl = environment.apiUrl;
  constructor(private http: HttpClient) {}

  getUserPermissions(): Observable<any> {
    return this.http.get(`${this.baseUrl}/me/permissions`);
  }
  isCollaborator(): Observable<boolean> {
    return this.http.get<boolean>(`${this.baseUrl}/is-collaborator`);
  }
}
