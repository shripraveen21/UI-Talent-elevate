import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { map } from 'rxjs/operators';
import { environment } from '../../../environments/environment';

@Injectable({ providedIn: 'root' })
export class TopicsService {
  private apiUrl = environment.apiUrl + '/topics/';

  constructor(private http: HttpClient) {}

  getTopics(): Observable<any[]> {
    return this.http.get<any[]>(this.apiUrl);
  }

  getTopicsCount(): Observable<number> {
    return this.http.get<any[]>(this.apiUrl).pipe(
      map(topics => topics.length)
    );
  }
}
