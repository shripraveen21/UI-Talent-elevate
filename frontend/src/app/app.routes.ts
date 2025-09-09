import { Routes } from '@angular/router';
import { LoginComponent } from './components/login/login.component';
import { DashboardComponent } from './components/dashboard/dashboard.component';
import { TestComponent } from './components/test/test.component';
import { ResultsComponent } from './components/results/results.component';
import { AgentChatComponent } from './components/epic-creation/agent-chat.component';
import { HomeComponent } from './components/home/home.component';
import { ManagerDashboardComponent } from './components/manager_dashboard/manager-dashboard/manager-dashboard.component';
import { authGuard } from './guards/auth.guard';


export const routes: Routes = [
  { path: '', redirectTo: 'home', pathMatch: 'full' },
  { path: 'home', component: HomeComponent },
  { path: 'login', component: LoginComponent },
  { path: 'agent-chat', component: AgentChatComponent },
   { path: 'dashboard', component: DashboardComponent },
  { path: 'test/:id', component: TestComponent },
  { path: 'results/:id', component: ResultsComponent },
{path:'directory',component:ManagerDashboardComponent,canActivate:[authGuard],data:{roles:['CapabilityLeader','ProductManager']}},
  {
    path: 'mcq-quiz',
    loadComponent: () => import('./components/mcq-quiz/mcq-quiz.component').then(m => m.McqQuizComponent)
  },
  {
    path: 'debug-exercise',
    loadComponent: () => import('./components/debug-exercise-form/debug-exercise-form.component').then(m => m.DebugExerciseFormComponent)
  },
  {
    path: 'add-techstack',
    loadComponent: () => import('./components/techstack-form/techstack-form.component').then(m => m.TechStackFormComponent)
  },
  { path: '**', redirectTo: 'home' },
];
