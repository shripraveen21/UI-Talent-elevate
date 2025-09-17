import { Injectable } from '@angular/core';
import { Observable, Subject } from 'rxjs';
import { environment } from '../../../environments/environment';
import { HttpClient } from '@angular/common/http';
import { MCQQuestion } from '../../components/mcq-question/mcq-question.component';

export interface QuizParams {
  tech_stack: { id: number; name: string }[]; // List of selected tech stacks with IDs
  topics: { name: string; level: 'beginner' | 'intermediate' | 'advanced'; topic_id: number; }[]; // Topics with IDs and levels
  num_questions: number;
  duration: number;
}

export interface AgentMessage {
  type: 'review' | 'final' | 'error';
  content: any;
  iteration?: number;
}

interface QuestionsDict {
  [key: string]: MCQQuestion;
}

@Injectable({
  providedIn: 'root'
})
export class McqAgentService {
  private ws?: WebSocket;
  private messageSubject = new Subject<AgentMessage>();

  constructor(private http: HttpClient) { }

  connect(params: QuizParams): Observable<AgentMessage> {
    if (this.ws) {
      this.ws.close();
    }
    this.ws = new WebSocket(environment.websocketUrl + '/ws/mcq-review');
    this.ws.onopen = () => {
      console.log("params are sent")
      this.ws?.send(JSON.stringify(params));
    };
    this.ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      this.messageSubject.next(data);
    };
    this.ws.onerror = (event) => {
      this.messageSubject.next({ type: 'error', content: 'WebSocket error' });
    };
    this.ws.onclose = () => {
      // Optionally notify close
    };
    return this.messageSubject.asObservable();
  }

  sendDecision(decision: string, feedback?: string) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({ decision, feedback }));
    }
  }

  close() {
    if (this.ws) {
      this.ws.close();
      this.ws = undefined;
    }
  }

  storeQuiz(quizParams: QuizParams, quizQuestions: any[]): Observable<any> {
    console.log(quizParams, quizQuestions, "printing before")
    const questionsDict: QuestionsDict = {};
    quizQuestions.forEach((q, i) => {
      questionsDict[`question${i + 1}`] = q;
    });
    const payload = {
      params: {
        tech_stack: quizParams.tech_stack.map(ts => ts.id)[0],
        topics: quizParams.topics.map(t => t.topic_id),
        num_questions: quizParams.num_questions,
        duration: quizParams.duration
      },
      questions: questionsDict
    };
    console.log("sent from frontend", payload);
    return this.http.post(environment.apiUrl + '/mcq/store', payload);
  }
}
