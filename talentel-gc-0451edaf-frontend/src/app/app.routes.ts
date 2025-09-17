import { Routes } from '@angular/router';
import { LoginComponent } from './components/login/login.component';
import { DashboardComponent } from './components/dashboard/dashboard.component';
import { TestComponent } from './components/test/test.component';
import { ResultsComponent } from './components/results/results.component';
import { AgentChatComponent } from './components/epic-creation/agent-chat.component';
import { HomeComponent } from './components/home/home.component';
import { ManagerDashboardComponent } from './components/manager_dashboard/manager-dashboard/manager-dashboard.component';
import { EmployeeDashboardComponent } from './components/dashboards/employee-dashboard.component';
import { CapabilityLeaderDashboardComponent } from './components/dashboards/capability-leader-dashboard.component';
import { DeliveryManagerDashboardComponent } from './components/dashboards/delivery-manager-dashboard.component';
import { CreateAssessmentComponent } from './components/create-assessment/create-assessment.component';
import { authGuard } from './guards/auth.guard';
import { LoginGuard } from './guards/login.guard';
import { SkillUpgradeComponent } from './components/skill-upgrade/skill-upgrade.component';
import { CanDeactivateTestGuard } from './guards/can-deactivate.guard';
import { ManageCollaboratorComponent } from './components/collaborator/manage-collaborator.component';
import { CollabGuard } from './guards/collab.guard';
import { TechStackFormComponent } from './components/techstack-form/techstack-form.component';
import { CollabTopicsComponent } from './components/collab-topics/collabtopics.component';
import { ProfilePageComponent } from './components/profile-page/profile-page.component';
import { DebugExerciseComponent } from './components/debug-gen/debug-gen.component';
import { HandsonWorkflowComponent } from './components/hands-on-gen/hands-on-gen.component';
import { DebugFeedbackComponent } from './components/debug-feedback/debug-feedback.component';


export const routes: Routes = [
  { path: '', redirectTo: 'home', pathMatch: 'full' },
  { path: 'home', component: HomeComponent,canActivate: [LoginGuard] },
  { path: 'login', component: LoginComponent ,canActivate: [LoginGuard]},
  { path: 'agent-chat', component: AgentChatComponent },
   { path: 'dashboard', component: DashboardComponent },
  { path: 'test/:id', component: TestComponent },
  { path: 'results/:id', component: ResultsComponent },
  { path: "debug-res", component: DebugFeedbackComponent},

  {path:'directory',component:ManagerDashboardComponent,canActivate: [CollabGuard], data: { permission: 'test_assign' }},
  { path: 'employee-dashboard', component: EmployeeDashboardComponent, canActivate: [authGuard], data: { roles: ['Employee'] } },
  { path: 'capability-leader-dashboard', component: CapabilityLeaderDashboardComponent, canActivate: [authGuard], data: { roles: ['CapabilityLeader'] } },
  { path: 'delivery-manager-dashboard', component: DeliveryManagerDashboardComponent, canActivate: [authGuard], data: { roles: ['DeliveryManager'] } },
  { path: 'create-assessment', component: CreateAssessmentComponent, canActivate: [CollabGuard], data: { permission: 'test_create' }},

  {
    path: 'mcq-quiz',
    loadComponent: () => import('./components/mcq-quiz/mcq-quiz.component').then(m => m.McqQuizComponent)
  },
  {
    path: 'skill-upgrade', component: SkillUpgradeComponent, canActivate:[authGuard]
  },
  {
    path: 'manage-collaborator',
    component: ManageCollaboratorComponent
  },
  {
    path: 'debug-gen', component: DebugExerciseComponent
  },
  {
    path: 'handson-gen', component: HandsonWorkflowComponent
  },
  {
    path:'feedback',
    loadComponent: () => import('./components/feedback-result/feedback-result.component').then(m => m.FeedbackResultComponent)
  },
  {
    path: 'debug-exercise',
    loadComponent: () => import('./components/debug-exercise-form/debug-exercise-form.component').then(m => m.DebugExerciseFormComponent)
  },

  {
    path: 'add-techstack', component: TechStackFormComponent, canActivate: [CollabGuard], data: { permission: 'topics' }
  },
  {
    path: 'collab-topics',
    component: CollabTopicsComponent,
    canActivate: [CollabGuard],
    data: { permission: 'topics' }
  },
  {
  path: 'debug-test/:id',
    loadComponent: () => import('./components/debug-test/debug-test.component').then(m => m.DebugTestComponent)
  },
  {
    path: 'debug-results/:id',
    loadComponent: () => import('./components/debug-results/debug-results.component').then(m => m.DebugResultsComponent)
  },

  {
    path: 'profile',
    loadComponent: () => import('./components/profile-page/profile-page.component').then(m => m.ProfilePageComponent)
  },
  { path: '**', redirectTo: 'home' },
];
