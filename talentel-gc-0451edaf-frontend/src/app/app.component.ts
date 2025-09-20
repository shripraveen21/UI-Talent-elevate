import { Component, OnInit, OnDestroy } from '@angular/core';
import { RouterOutlet, Router, NavigationEnd } from '@angular/router';
import { NavbarComponent } from './components/shared/navbar/navbar.component';
import { ToastContainerComponent } from './components/shared/toast/toast-container.component';
import { CommonModule } from '@angular/common';
import { Subscription } from 'rxjs';
import { filter } from 'rxjs/operators';

@Component({
  selector: 'app-root',
  imports: [RouterOutlet, NavbarComponent, ToastContainerComponent, CommonModule],
  templateUrl: './app.component.html',
  styleUrl: './app.component.css'
})
export class AppComponent implements OnInit, OnDestroy {
  title = 'frontend';
  shouldShowNavbar = true;
  private routerSubscription?: Subscription;
  
  // Routes where navbar should be hidden
  private hiddenRoutes = ['/', '/home', '/login'];

  constructor(private router: Router) {}

  ngOnInit() {
    // Check initial route
    this.checkNavbarVisibility();
    
    // Subscribe to route changes
    this.routerSubscription = this.router.events
      .pipe(filter(event => event instanceof NavigationEnd))
      .subscribe(() => {
        this.checkNavbarVisibility();
      });
  }

  ngOnDestroy() {
    if (this.routerSubscription) {
      this.routerSubscription.unsubscribe();
    }
  }

  private checkNavbarVisibility() {
    const currentUrl = this.router.url;
    this.shouldShowNavbar = !this.hiddenRoutes.includes(currentUrl);
  }
}