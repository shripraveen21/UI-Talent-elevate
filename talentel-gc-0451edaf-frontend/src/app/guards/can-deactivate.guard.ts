import { Injectable } from '@angular/core';
import { CanDeactivate } from '@angular/router';
import { TestComponent } from '../components/test/test.component';


@Injectable({ providedIn: 'root' })
export class CanDeactivateTestGuard implements CanDeactivate<TestComponent> {
  canDeactivate(component: TestComponent): boolean {
    if (!component.submitted) {
      alert('You cannot leave the test until you submit.');
      return false;
    }
    return true;
  }
}
