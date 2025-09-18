import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { Employee } from '../../models/interface/employee';
import { environment } from '../../../environments/environment';

@Injectable({
  providedIn: 'root'
})
export class EmployeeService {

  private apiUrl = environment.apiUrl + '/employees';
  private filterOptionsUrl = environment.apiUrl + '/employee-filter-options';
  private profileUrl = environment.apiUrl + '/employee/profile';

  constructor(private http: HttpClient) { }

  getEmployees(params: any): Observable<any> {
    return this.http.get<any>(this.apiUrl, { params });
  }

  getEmployeeFilterOptions(): Observable<any> {
    return this.http.get<any>(this.filterOptionsUrl);
  }

  getProfile(): Observable<any> {
    return this.http.get<any>(this.profileUrl);
  }
}
