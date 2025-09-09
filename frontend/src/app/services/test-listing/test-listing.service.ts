import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';

@Injectable({
  providedIn: 'root'
})
export class TestListingService {
  private apiUrl = environment.apiUrl + '/tests';

  constructor(private http: HttpClient) {}

  getTests(params: any = {}): Observable<any> {
    return this.http.get<any>(this.apiUrl, { params });
  }
}
