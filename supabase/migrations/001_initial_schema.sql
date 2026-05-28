-- profiles: extends Supabase auth.users
create table profiles (
  id uuid references auth.users primary key,
  full_name text,
  target_role text,
  experience_years int,
  created_at timestamptz default now()
);

-- sessions: one per interview attempt
create table sessions (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references profiles(id) on delete cascade,
  mode text not null check (mode in ('mock', 'rapid', 'custom')),
  job_description text,
  target_company text,
  role text,
  started_at timestamptz default now(),
  completed_at timestamptz,
  overall_score int,
  weakness_tags text[]
);

-- questions: generated per session
create table questions (
  id uuid primary key default gen_random_uuid(),
  session_id uuid references sessions(id) on delete cascade,
  question_text text not null,
  question_type text check (question_type in ('technical','behavioural','situational','rapid')),
  order_index int,
  created_at timestamptz default now()
);

-- answers: user responses with STAR scores
create table answers (
  id uuid primary key default gen_random_uuid(),
  question_id uuid references questions(id) on delete cascade,
  user_id uuid references profiles(id),
  answer_text text,
  answer_audio_url text,
  star_situation_score int,  -- 0-25 each
  star_task_score int,
  star_action_score int,
  star_result_score int,
  total_score int,            -- 0-100
  feedback_text text,
  ideal_answer text,
  weakness_tags text[],
  answered_at timestamptz default now()
);

-- community_questions: crowdsourced real interview Q's
create table community_questions (
  id uuid primary key default gen_random_uuid(),
  submitted_by uuid references profiles(id),
  company text,
  role text,
  question_text text not null,
  question_type text,
  verified boolean default false,
  upvotes int default 0,
  created_at timestamptz default now()
);

-- weakness_summary: aggregated per user across all sessions
create table weakness_summary (
  user_id uuid references profiles(id) primary key,
  top_weaknesses jsonb,  -- {"missing_result": 12, "over_explains": 8}
  total_sessions int default 0,
  total_questions_answered int default 0,
  updated_at timestamptz default now()
);

-- RLS
alter table profiles enable row level security;
alter table sessions enable row level security;
alter table questions enable row level security;
alter table answers enable row level security;
alter table community_questions enable row level security;
alter table weakness_summary enable row level security;

create policy "own profile" on profiles for all using (auth.uid() = id);
create policy "own sessions" on sessions for all using (auth.uid() = user_id);
create policy "own session questions" on questions for select using (
  session_id in (select id from sessions where user_id = auth.uid())
);
create policy "own answers" on answers for all using (auth.uid() = user_id);
create policy "public verified questions" on community_questions for select using (verified = true);
create policy "submit questions" on community_questions for insert with check (auth.uid() = submitted_by);
create policy "own weakness summary" on weakness_summary for all using (auth.uid() = user_id);
