import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders, HttpErrorResponse } from '@angular/common/http';
import { Observable, throwError, of } from 'rxjs';
import { catchError, map, switchMap, tap } from 'rxjs/operators';
import { environment } from '../../../environments/environment';

/**
 * LoginResponse matches backend /login and /me endpoints.
 */
export interface LoginResponse {
  token: string;
  user: { id: number; name: string; email: string };
  roles: string[];
}

@Injectable({
  providedIn: 'root',
})
export class LoginService {
  /**
   * API URL is loaded from environment.ts for flexibility.
   */
  private apiUrl = environment.apiUrl;

  constructor(private http: HttpClient) {}

  login(email: string, password: string): Observable<LoginResponse> {
    const loginPayload = { email, password };
    // Logging login attempt
    console.info('[LoginService] Attempting login for:', email);

    return this.http.post<{ access_token: string; token_type: string }>(
      `${environment.apiUrl}/login`,
      loginPayload
    ).pipe(
      tap(res => {
        // Structured logging
        console.info('[LoginService] Login response:', JSON.stringify(res));
      }),
      switchMap(res => {
        const token = res.access_token;
        // Store token in localStorage
        localStorage.setItem('token', token);

        // Fetch user info from /getCurrentUser endpoint
        const headers = new HttpHeaders({
          Authorization: `Bearer ${token}`,
        });
        return this.http.get<any>(`${environment.apiUrl}/getCurrentUser`, { headers }).pipe(
          map(user => {
            // Store user info in localStorage
            localStorage.setItem('user', JSON.stringify(user));
            // Logging user info
            console.info('[LoginService] User info:', JSON.stringify(user));
            // Compose LoginResponse
            return {
              token,
              user: {
                id: user.user_id,
                name: user.name,
                email: user.email,
              },
              roles: [user.role], // Assuming single role, adjust if needed
            } as LoginResponse;
          })
        );
      }),
      catchError((error: HttpErrorResponse) => {
        // Custom error handling
        let message = 'Unknown error';
        if (error.status === 401) {
          message = 'Invalid credentials';
        } else if (error.error?.detail) {
          message = error.error.detail;
        } else if (error.message) {
          message = error.message;
        }
        // Structured error logging
        console.error('[LoginService] Login error:', JSON.stringify(error));
        return throwError(() => new Error(message));
      })
    );
  }

  /**
   * Returns current user from localStorage, or null if not logged in.
   */
  getCurrentUser(): { id: number; name: string; email: string; role?: string } | null {
    const raw = localStorage.getItem('user');
    return raw ? JSON.parse(raw) : null;
  }

  /**
   * Returns the current user's role, or null if not logged in.
   */
  getUserRole(): string | null {
    const user = this.getCurrentUser();
    // Support both user.role and user.roles[0]
    if (user && (user as any).role) {
      return (user as any).role;
    }
    if (user && Array.isArray((user as any).roles) && (user as any).roles.length > 0) {
      return (user as any).roles[0];
    }
    return null;
  }

  isAuthenticated(): boolean {
    return !!localStorage.getItem('token');
  }
}
