import { CanActivateFn, Router } from '@angular/router';
import { LoginService } from '../services/login/login.service';
import { inject } from '@angular/core';

const allowedRoles = [
  'DeliveryManager',
  'DeliveryLeader',
  'ProductManager',
  'CapabilityLeader'
];

export const multiRoleGuard: CanActivateFn = (route, state) => {
  const router = inject(Router);
  const auth = inject(LoginService);

  if (!auth.isAuthenticated()) {
    router.navigate(['/login']);
    return false;
  }
  if (!allowedRoles.includes(auth.getUserRole() || '')) {
    router.navigate(['/unauthorized']);
    return false;
  }
  return true;
};
