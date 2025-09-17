import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';
import { map } from 'rxjs/operators';


@Injectable({
  providedIn: 'root'
})
export class DebugTestService {
  private baseUrl = environment.apiUrl + '/tests';

  constructor(private http: HttpClient) {}

  getDebugId(testId: number): Observable<number | null> {
    const url = `${this.baseUrl}/${testId}/debug-id`;
    return this.http.get<{ debug_id: number | null }>(url)
      .pipe(
        map((res: { debug_id: number | null }) => res.debug_id)
      );
  }
}
