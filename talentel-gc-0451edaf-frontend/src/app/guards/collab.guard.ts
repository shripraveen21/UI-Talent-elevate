import { Injectable } from '@angular/core';
import { CanActivate, ActivatedRouteSnapshot, RouterStateSnapshot, Router } from '@angular/router';
import { Observable } from 'rxjs';
import { map } from 'rxjs/operators';
import { PermissionsService } from '../services/auth/permissions.service';

@Injectable({ providedIn: 'root' })
export class CollabGuard implements CanActivate {
  constructor(private permissionsService: PermissionsService, private router: Router) {}

  canActivate(route: ActivatedRouteSnapshot, state: RouterStateSnapshot): Observable<boolean> {
    const requiredPermission = route.data['permission'];
    return this.permissionsService.getUserPermissions().pipe(
      map(permissions => {
        if (permissions.role === 'CapabilityLeader' || permissions.role === 'ProductManager') {
          return true;
        }
        if (permissions.isCollaborator && permissions[requiredPermission]) {
          return true;
        }
        // Optionally, show a toast or redirect
        this.router.navigate(['/employee-dashboard']);
        return false;
      })
    );
  }
}
