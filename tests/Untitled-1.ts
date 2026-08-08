compliance-tracker/
├── backend/
│   ├── prisma/
│   │   └── schema.prisma
│   ├── src/
│   │   ├── middleware/
│   │   │   ├── auth.ts
│   │   │   └── role.ts
│   │   ├── routes/
│   │   │   ├── auth.ts
│   │   │   ├── compliances.ts
│   │   │   ├── master.ts
│   │   │   ├── users.ts
│   │   │   └── audits.ts
│   │   ├── controllers/
│   │   │   ├── auth.controller.ts
│   │   │   ├── compliance.controller.ts
│   │   │   ├── master.controller.ts
│   │   │   └── audit.controller.ts
│   │   └── index.ts
│   ├── .env
│   └── package.json
│
└── frontend/
    ├── src/
    │   ├── api/
    │   │   ├── client.ts
    │   │   ├── auth.ts
    │   │   ├── compliances.ts
    │   │   ├── master.ts
    │   │   └── audits.ts
    │   ├── components/
    │   │   ├── Layout.tsx
    │   │   ├── Navbar.tsx
    │   │   ├── Sidebar.tsx
    │   │   ├── StatusBadge.tsx
    │   │   ├── ComplianceTable.tsx
    │   │   ├── MasterDataModal.tsx
    │   │   └── DashboardStats.tsx
    │   ├── pages/
    │   │   ├── Login.tsx
    │   │   ├── Dashboard.tsx
    │   │   ├── ComplianceTracker.tsx
    │   │   ├── MasterData.tsx
    │   │   └── AuditLog.tsx
    │   ├── context/
    │   │   └── AuthContext.tsx
    │   ├── App.tsx
    │   └── main.tsx
    ├── .env
    └── vite.config.ts
DATABASE_URL="postgresql://postgres:password@localhost:5432/compliance_db"
JWT_SECRET="your-very-strong-secret-key-here"
PORT=4000

generator client {
  provider = "prisma-client-js"
}

datasource db {
  provider = "postgresql"
  url      = env("DATABASE_URL")
}

model User {
  id        String   @id @default(uuid())
  name      String
  email     String   @unique
  password  String
  role      Role     @default(USER_1)
  createdAt DateTime @default(now())

  compliances     Compliance[] @relation("ResponsibleUser")
  reviewingItems  Compliance[] @relation("ReviewerUser")
  auditLogs       AuditLog[]
}

enum Role {
  CFO
  USER_1
  USER_2
  USER_3
}

model ComplianceCategory {
  id          String       @id @default(uuid())
  name        String       @unique
  description String?
  compliances Compliance[]
}

model Compliance {
  id                 String             @id @default(uuid())
  complianceArea     String
  category           ComplianceCategory @relation(fields: [categoryId], references: [id])
  categoryId         String
  applicableLaw      String
  statuteRef         String?
  actionName         String
  dueDate            DateTime
  frequency          Frequency
  applicability      String
  status             ComplianceStatus   @default(NOT_STARTED)
  responsibleUser    User               @relation("ResponsibleUser", fields: [responsibleUserId], references: [id])
  responsibleUserId  String
  reviewerUser       User               @relation("ReviewerUser", fields: [reviewerUserId], references: [id])
  reviewerUserId     String
  penalty            String?
  internalCutoff     DateTime?
  remarks            String?
  sharedWith         String[]
  createdAt          DateTime           @default(now())
  updatedAt          DateTime           @updatedAt
  auditLogs          AuditLog[]
}

enum Frequency {
  MONTHLY
  QUARTERLY
  HALF_YEARLY
  ANNUAL
  EVENT_BASED
}

enum ComplianceStatus {
  NOT_STARTED
  IN_PROGRESS
  PENDING_REVIEW
  COMPLETED
  DEFERRED
}

model AuditLog {
  id           String     @id @default(uuid())
  compliance   Compliance @relation(fields: [complianceId], references: [id])
  complianceId String
  user         User       @relation(fields: [userId], references: [id])
  userId       String
  action       String
  oldValue     String?
  newValue     String?
  createdAt    DateTime   @default(now())
}
import express from 'express';
import cors from 'cors';
import dotenv from 'dotenv';
import authRoutes from './routes/auth';
import complianceRoutes from './routes/compliances';
import masterRoutes from './routes/master';
import userRoutes from './routes/users';
import auditRoutes from './routes/audits';

dotenv.config();

const app = express();

app.use(cors({ origin: 'http://localhost:5173', credentials: true }));
app.use(express.json());

app.use('/api/auth', authRoutes);
app.use('/api/compliances', complianceRoutes);
app.use('/api/master', masterRoutes);
app.use('/api/users', userRoutes);
app.use('/api/audits', auditRoutes);

app.listen(process.env.PORT || 4000, () => {
  console.log(`Server running on port ${process.env.PORT || 4000}`);
});

import { Request, Response, NextFunction } from 'express';
import jwt from 'jsonwebtoken';

export interface AuthRequest extends Request {
  user?: { id: string; role: string; email: string };
}

export function authenticate(req: AuthRequest, res: Response, next: NextFunction) {
  const authHeader = req.headers.authorization;
  if (!authHeader?.startsWith('Bearer ')) {
    return res.status(401).json({ message: 'Unauthorized' });
  }

  const token = authHeader.split(' ')[1];
  try {
    const payload = jwt.verify(token, process.env.JWT_SECRET!) as {
      id: string;
      role: string;
      email: string;
    };
    req.user = payload;
    next();
  } catch {
    return res.status(401).json({ message: 'Invalid token' });
  }
}

import { Response, NextFunction } from 'express';
import { AuthRequest } from './auth';

export function requireCFO(req: AuthRequest, res: Response, next: NextFunction) {
  if (req.user?.role !== 'CFO') {
    return res.status(403).json({ message: 'CFO access only' });
  }
  next();
}

import { Router } from 'express';
import { login } from '../controllers/auth.controller';

const router = Router();
router.post('/login', login);
export default router;

import { Request, Response } from 'express';
import { PrismaClient } from '@prisma/client';
import bcrypt from 'bcryptjs';
import jwt from 'jsonwebtoken';

const prisma = new PrismaClient();

export async function login(req: Request, res: Response) {
  const { email, password } = req.body;

  const user = await prisma.user.findUnique({ where: { email } });
  if (!user) return res.status(401).json({ message: 'Invalid credentials' });

  const valid = await bcrypt.compare(password, user.password);
  if (!valid) return res.status(401).json({ message: 'Invalid credentials' });

  const token = jwt.sign(
    { id: user.id, role: user.role, email: user.email },
    process.env.JWT_SECRET!,
    { expiresIn: '8h' }
  );

  return res.json({
    token,
    user: { id: user.id, name: user.name, email: user.email, role: user.role },
  });
}

import { Response } from 'express';
import { PrismaClient } from '@prisma/client';
import { AuthRequest } from '../middleware/auth';

const prisma = new PrismaClient();

export async function getCompliances(req: AuthRequest, res: Response) {
  const user = req.user!;
  const where =
    user.role === 'CFO'
      ? {}
      : {
          OR: [
            { responsibleUserId: user.id },
            { sharedWith: { has: user.id } },
          ],
        };

  const compliances = await prisma.compliance.findMany({
    where,
    include: {
      category: true,
      responsibleUser: { select: { id: true, name: true, role: true } },
      reviewerUser: { select: { id: true, name: true, role: true } },
    },
    orderBy: { dueDate: 'asc' },
  });

  return res.json(compliances);
}

export async function updateStatus(req: AuthRequest, res: Response) {
  const { id } = req.params;
  const { status, remarks } = req.body;
  const user = req.user!;

  const compliance = await prisma.compliance.findUnique({ where: { id } });
  if (!compliance) return res.status(404).json({ message: 'Not found' });

  const canEdit =
    user.role === 'CFO' || compliance.responsibleUserId === user.id;

  if (!canEdit)
    return res.status(403).json({ message: 'Permission denied' });

  const oldStatus = compliance.status;
  const updated = await prisma.compliance.update({
    where: { id },
    data: { status, remarks },
  });

  await prisma.auditLog.create({
    data: {
      complianceId: id,
      userId: user.id,
      action: 'STATUS_UPDATE',
      oldValue: oldStatus,
      newValue: status,
    },
  });

  return res.json(updated);
}

export async function createCompliance(req: AuthRequest, res: Response) {
  const data = req.body;
  const compliance = await prisma.compliance.create({ data });
  return res.status(201).json(compliance);
}

export async function updateCompliance(req: AuthRequest, res: Response) {
  const { id } = req.params;
  const data = req.body;
  const updated = await prisma.compliance.update({ where: { id }, data });
  return res.json(updated);
}

export async function deleteCompliance(req: AuthRequest, res: Response) {
  const { id } = req.params;
  await prisma.compliance.delete({ where: { id } });
  return res.json({ message: 'Deleted' });
}
import { Router } from 'express';
import { authenticate } from '../middleware/auth';
import { requireCFO } from '../middleware/role';
import {
  getCompliances,
  updateStatus,
  createCompliance,
  updateCompliance,
  deleteCompliance,
} from '../controllers/compliance.controller';

const router = Router();

router.use(authenticate);

router.get('/', getCompliances);
router.patch('/:id/status', updateStatus);
router.post('/', requireCFO, createCompliance);
router.put('/:id', requireCFO, updateCompliance);
router.delete('/:id', requireCFO, deleteCompliance);

export default router;

import { Response } from 'express';
import { PrismaClient } from '@prisma/client';
import { AuthRequest } from '../middleware/auth';

const prisma = new PrismaClient();

export async function getCategories(_req: AuthRequest, res: Response) {
  const categories = await prisma.complianceCategory.findMany();
  return res.json(categories);
}

export async function createCategory(req: AuthRequest, res: Response) {
  const { name, description } = req.body;
  const category = await prisma.complianceCategory.create({
    data: { name, description },
  });
  return res.status(201).json(category);
}

export async function updateCategory(req: AuthRequest, res: Response) {
  const { id } = req.params;
  const { name, description } = req.body;
  const updated = await prisma.complianceCategory.update({
    where: { id },
    data: { name, description },
  });
  return res.json(updated);
}

export async function deleteCategory(req: AuthRequest, res: Response) {
  const { id } = req.params;
  await prisma.complianceCategory.delete({ where: { id } });
  return res.json({ message: 'Deleted' });
}

import { Router } from 'express';
import { authenticate } from '../middleware/auth';
import { requireCFO } from '../middleware/role';
import {
  getCategories,
  createCategory,
  updateCategory,
  deleteCategory,
} from '../controllers/master.controller';

const router = Router();

router.use(authenticate);

router.get('/categories', getCategories);
router.post('/categories', requireCFO, createCategory);
router.put('/categories/:id', requireCFO, updateCategory);
router.delete('/categories/:id', requireCFO, deleteCategory);

export default router;

VITE_API_BASE_URL=http://localhost:4000

import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:4000',
        changeOrigin: true,
        secure: false,
      },
    },
  },
});

const BASE = import.meta.env.VITE_API_BASE_URL || '';

export async function apiRequest<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = localStorage.getItem('token');
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    ...(options.headers || {}),
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };

  const res = await fetch(`${BASE}${path}`, { ...options, headers });
  const isJson = res.headers.get('content-type')?.includes('application/json');
  const data = isJson ? await res.json() : null;

  if (!res.ok) throw new Error(data?.message || 'Request failed');
  return data as T;
}
import { apiRequest } from './client';

export type ComplianceStatus =
  | 'NOT_STARTED' | 'IN_PROGRESS' | 'PENDING_REVIEW' | 'COMPLETED' | 'DEFERRED';

export type Frequency =
  | 'MONTHLY' | 'QUARTERLY' | 'HALF_YEARLY' | 'ANNUAL' | 'EVENT_BASED';

export interface Compliance {
  id: string;
  complianceArea: string;
  categoryId: string;
  applicableLaw: string;
  statuteRef?: string;
  actionName: string;
  dueDate: string;
  frequency: Frequency;
  applicability: string;
  status: ComplianceStatus;
  responsibleUserId: string;
  reviewerUserId: string;
  penalty?: string;
  internalCutoff?: string;
  remarks?: string;
  sharedWith: string[];
}

export const getCompliances = () => apiRequest<Compliance[]>('/api/compliances');

export const updateStatus = (id: string, status: ComplianceStatus, remarks?: string) =>
  apiRequest<Compliance>(`/api/compliances/${id}/status`, {
    method: 'PATCH',
    body: JSON.stringify({ status, remarks }),
  });

export const createCompliance = (data: Partial<Compliance>) =>
  apiRequest<Compliance>('/api/compliances', {
    method: 'POST',
    body: JSON.stringify(data),
  });

export const updateCompliance = (id: string, data: Partial<Compliance>) =>
  apiRequest<Compliance>(`/api/compliances/${id}`, {
    method: 'PUT',
    body: JSON.stringify(data),
  });

export const deleteCompliance = (id: string) =>
  apiRequest(`/api/compliances/${id}`, { method: 'DELETE' });

import { createContext, useContext, useState, ReactNode } from 'react';
import { apiRequest } from '../api/client';

interface User {
  id: string;
  name: string;
  email: string;
  role: 'CFO' | 'USER_1' | 'USER_2' | 'USER_3';
}

interface AuthContextType {
  user: User | null;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  isCFO: boolean;
}

const AuthContext = createContext<AuthContextType | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(() => {
    const raw = localStorage.getItem('user');
    return raw ? JSON.parse(raw) : null;
  });

  const login = async (email: string, password: string) => {
    const res = await apiRequest<{ token: string; user: User }>('/api/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    });
    localStorage.setItem('token', res.token);
    localStorage.setItem('user', JSON.stringify(res.user));
    setUser(res.user);
  };

  const logout = () => {
    localStorage.clear();
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, login, logout, isCFO: user?.role === 'CFO' }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
};

import { useEffect, useState } from 'react';
import { getCompliances, Compliance } from '../api/compliances';
import { useAuth } from '../context/AuthContext';

const STATUS_COLORS: Record<string, string> = {
  NOT_STARTED: '#9ca3af',
  IN_PROGRESS: '#f59e0b',
  PENDING_REVIEW: '#8b5cf6',
  COMPLETED: '#16a34a',
  DEFERRED: '#dc2626',
};

const STATUS_LABELS: Record<string, string> = {
  NOT_STARTED: 'Not Started',
  IN_PROGRESS: 'In Progress',
  PENDING_REVIEW: 'Pending Review',
  COMPLETED: 'Completed',
  DEFERRED: 'Deferred',
};

export default function Dashboard() {
  const { user } = useAuth();
  const [compliances, setCompliances] = useState<Compliance[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getCompliances()
      .then(setCompliances)
      .finally(() => setLoading(false));
  }, []);

  const today = new Date();

  const stats = {
    total: compliances.length,
    completed: compliances.filter((c) => c.status === 'COMPLETED').length,
    inProgress: compliances.filter((c) => c.status === 'IN_PROGRESS').length,
    overdue: compliances.filter(
      (c) => new Date(c.dueDate) < today && c.status !== 'COMPLETED'
    ).length,
    dueThisWeek: compliances.filter((c) => {
      const d = new Date(c.dueDate);
      const diff = (d.getTime() - today.getTime()) / (1000 * 60 * 60 * 24);
      return diff >= 0 && diff <= 7 && c.status !== 'COMPLETED';
    }).length,
  };

  if (loading) return <p style={{ padding: 24 }}>Loading dashboard...</p>;

  return (
    <div style={{ padding: 24 }}>
      <h2>Welcome, {user?.name} 👋</h2>
      <p style={{ color: '#6b7280' }}>Role: {user?.role}</p>

      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
          gap: 16,
          marginTop: 24,
        }}
      >
        {[
          { label: 'Total Compliances', value: stats.total, color: '#2563eb' },
          { label: 'Completed', value: stats.completed, color: '#16a34a' },
          { label: 'In Progress', value: stats.inProgress, color: '#f59e0b' },
          { label: 'Overdue', value: stats.overdue, color: '#dc2626' },
          { label: 'Due This Week', value: stats.dueThisWeek, color: '#7c3aed' },
        ].map((stat) => (
          <div
            key={stat.label}
            style={{
              background: 'white',
              borderRadius: 12,
              padding: '20px 24px',
              boxShadow: '0 4px 12px rgba(0,0,0,0.08)',
              borderLeft: `4px solid ${stat.color}`,
            }}
          >
            <div style={{ fontSize: 32, fontWeight: 700, color: stat.color }}>
              {stat.value}
            </div>
            <div style={{ fontSize: 14, color: '#374151', marginTop: 4 }}>{stat.label}</div>
          </div>
        ))}
      </div>

      <h3 style={{ marginTop: 32 }}>Status Breakdown</h3>
      <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap', marginTop: 12 }}>
        {Object.keys(STATUS_LABELS).map((s) => {
          const count = compliances.filter((c) => c.status === s).length;
          return (
            <div
              key={s}
              style={{
                background: STATUS_COLORS[s],
                color: 'white',
                borderRadius: 999,
                padding: '8px 18px',
                fontSize: 14,
                fontWeight: 600,
              }}
            >
              {STATUS_LABELS[s]}: {count}
            </div>
          );
        })}
      </div>

      <h3 style={{ marginTop: 32 }}>⚠️ Upcoming Due (Next 7 Days)</h3>
      {compliances
        .filter((c) => {
          const d = new Date(c.dueDate);
          const diff = (d.getTime() - today.getTime()) / (1000 * 60 * 60 * 24);
          return diff >= 0 && diff <= 7 && c.status !== 'COMPLETED';
        })
        .map((c) => (
          <div
            key={c.id}
            style={{
              background: '#fff7ed',
              border: '1px solid #fed7aa',
              borderRadius: 10,
              padding: '12px 16px',
              marginTop: 10,
              fontSize: 14,
            }}
          >
            <strong>{c.actionName}</strong> — {c.applicableLaw} — Due:{' '}
            {new Date(c.dueDate).toLocaleDateString('en-IN')}
          </div>
        ))}
    </div>
  );
}

import { useEffect, useState } from 'react';
import {
  getCompliances,
  updateStatus,
  Compliance,
  ComplianceStatus,
} from '../api/compliances';
import { useAuth } from '../context/AuthContext';

const STATUS_OPTIONS: ComplianceStatus[] = [
  'NOT_STARTED', 'IN_PROGRESS', 'PENDING_REVIEW', 'COMPLETED', 'DEFERRED',
];

const STATUS_LABELS: Record<ComplianceStatus, string> = {
  NOT_STARTED: 'Not Started',
  IN_PROGRESS: 'In Progress',
  PENDING_REVIEW: 'Pending Review',
  COMPLETED: 'Completed',
  DEFERRED: 'Deferred',
};

const STATUS_COLORS: Record<ComplianceStatus, string> = {
  NOT_STARTED: '#9ca3af',
  IN_PROGRESS: '#f59e0b',
  PENDING_REVIEW: '#8b5cf6',
  COMPLETED: '#16a34a',
  DEFERRED: '#dc2626',
};

export default function ComplianceTracker() {
  const { user, isCFO } = useAuth();
  const [data, setData] = useState<Compliance[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [filterStatus, setFilterStatus] = useState('');
  const [filterArea, setFilterArea] = useState('');

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    const items = await getCompliances();
    setData(items);
    setLoading(false);
  };

  const handleStatusChange = async (id: string, status: ComplianceStatus) => {
    await updateStatus(id, status);
    await loadData();
  };

  const today = new Date();

  const filtered = data.filter((c) => {
    const q = search.toLowerCase();
    const matchSearch =
      !q ||
      c.complianceArea.toLowerCase().includes(q) ||
      c.applicableLaw.toLowerCase().includes(q) ||
      c.actionName.toLowerCase().includes(q);
    const matchStatus = !filterStatus || c.status === filterStatus;
    const matchArea = !filterArea || c.complianceArea === filterArea;
    return matchSearch && matchStatus && matchArea;
  });

  const areas = [...new Set(data.map((c) => c.complianceArea))];

  if (loading) return <p style={{ padding: 24 }}>Loading compliances...</p>;

  return (
    <div style={{ padding: 24 }}>
      <h2>Compliance Tracker</h2>

      <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap', marginBottom: 16 }}>
        <input
          placeholder="Search action, law, area..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          style={inputStyle}
        />
        <select
          value={filterStatus}
          onChange={(e) => setFilterStatus(e.target.value)}
          style={inputStyle}
        >
          <option value="">All Statuses</option>
          {STATUS_OPTIONS.map((s) => (
            <option key={s} value={s}>{STATUS_LABELS[s]}</option>
          ))}
        </select>
        <select
          value={filterArea}
          onChange={(e) => setFilterArea(e.target.value)}
          style={inputStyle}
        >
          <option value="">All Areas</option>
          {areas.map((a) => (
            <option key={a} value={a}>{a}</option>
          ))}
        </select>
      </div>

      <div style={{ overflowX: 'auto' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', minWidth: 1200, fontSize: 13 }}>
          <thead>
            <tr style={{ background: '#f9fafb' }}>
              {[
                'Area', 'Applicable Law', 'Statute Ref', 'Action', 'Due Date',
                'Frequency', 'Status', 'Responsible', 'Reviewer',
                'Penalty', 'Internal Cutoff', 'Remarks',
              ].map((h) => (
                <th key={h} style={thStyle}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {filtered.map((row) => {
              const isOverdue =
                new Date(row.dueDate) < today && row.status !== 'COMPLETED';
              const canEdit = isCFO || row.responsibleUserId === user?.id;

              return (
                <tr
                  key={row.id}
                  style={{
                    background: isOverdue ? '#fff1f2' : 'white',
                    borderBottom: '1px solid #e5e7eb',
                  }}
                >
                  <td style={tdStyle}>{row.complianceArea}</td>
                  <td style={tdStyle}>{row.applicableLaw}</td>
                  <td style={tdStyle}>{row.statuteRef || '—'}</td>
                  <td style={tdStyle}>{row.actionName}</td>
                  <td style={{ ...tdStyle, color: isOverdue ? '#dc2626' : 'inherit', fontWeight: isOverdue ? 700 : 400 }}>
                    {new Date(row.dueDate).toLocaleDateString('en-IN')}
                    {isOverdue && ' ⚠️'}
                  </td>
                  <td style={tdStyle}>{row.frequency}</td>
                  <td style={tdStyle}>
                    {canEdit ? (
                      <select
                        value={row.status}
                        onChange={(e) =>
                          handleStatusChange(row.id, e.target.value as ComplianceStatus)
                        }
                        style={{
                          background: STATUS_COLORS[row.status],
                          color: 'white',
                          border: 'none',
                          borderRadius: 999,
                          padding: '6px 12px',
                          fontWeight: 700,
                          cursor: 'pointer',
                          fontSize: 12,
                        }}
                      >
                        {STATUS_OPTIONS.map((s) => (
                          <option key={s} value={s} style={{ background: STATUS_COLORS[s] }}>
                            {STATUS_LABELS[s]}
                          </option>
                        ))}
                      </select>
                    ) : (
                      <span
                        style={{
                          background: STATUS_COLORS[row.status],
                          color: 'white',
                          borderRadius: 999,
                          padding: '6px 12px',
                          fontWeight: 700,
                          fontSize: 12,
                        }}
                      >
                        {STATUS_LABELS[row.status]}
                      </span>
                    )}
                  </td>
                  <td style={tdStyle}>{row.responsibleUserId}</td>
                  <td style={tdStyle}>{row.reviewerUserId}</td>
                  <td style={tdStyle}>{row.penalty || '—'}</td>
                  <td style={tdStyle}>
                    {row.internalCutoff
                      ? new Date(row.internalCutoff).toLocaleDateString('en-IN')
                      : '—'}
                  </td>
                  <td style={tdStyle}>{row.remarks || '—'}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}

const inputStyle: React.CSSProperties = {
  padding: '10px 14px',
  borderRadius: 10,
  border: '1px solid #d1d5db',
  fontSize: 14,
  minWidth: 200,
};

const thStyle: React.CSSProperties = {
  padding: '10px 12px',
  textAlign: 'left',
  borderBottom: '2px solid #e5e7eb',
  fontWeight: 700,
  fontSize: 13,
};

const tdStyle: React.CSSProperties = {
  padding: '10px 12px',
  verticalAlign: 'top',
  fontSize: 13,
};

import { useEffect, useState } from 'react';
import { apiRequest } from '../api/client';
import { useAuth } from '../context/AuthContext';

interface Category {
  id: string;
  name: string;
  description?: string;
}

export default function MasterData() {
  const { isCFO } = useAuth();
  const [categories, setCategories] = useState<Category[]>([]);
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [editId, setEditId] = useState<string | null>(null);

  const load = async () => {
    const data = await apiRequest<Category[]>('/api/master/categories');
    setCategories(data);
  };

  useEffect(() => { load(); }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (editId) {
      await apiRequest(`/api/master/categories/${editId}`, {
        method: 'PUT',
        body: JSON.stringify({ name, description }),
      });
    } else {
      await apiRequest('/api/master/categories', {
        method: 'POST',
        body: JSON.stringify({ name, description }),
      });
    }
    setName('');
    setDescription('');
    setEditId(null);
    load();
  };

  const handleDelete = async (id: string) => {
    if (!confirm('Delete this category?')) return;
    await apiRequest(`/api/master/categories/${id}`, { method: 'DELETE' });
    load();
  };

  if (!isCFO) return (
    <div style={{ padding: 24 }}>
      <h2>Master Data</h2>
      <p style={{ color: '#dc2626' }}>⛔ Only CFO can access master data.</p>
    </div>
  );

  return (
    <div style={{ padding: 24 }}>
      <h2>Master Data — Compliance Categories</h2>
      <p style={{ color: '#6b7280' }}>CFO only — manage compliance categories here.</p>

      <form onSubmit={handleSubmit} style={{ display: 'flex', gap: 12, flexWrap: 'wrap', marginBottom: 24 }}>
        <input
          required
          placeholder="Category name"
          value={name}
          onChange={(e) => setName(e.target.value)}
          style={inputStyle}
        />
        <input
          placeholder="Description (optional)"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          style={{ ...inputStyle, minWidth: 300 }}
        />
        <button type="submit" style={btnPrimary}>
          {editId ? 'Update' : 'Add Category'}
        </button>
        {editId && (
          <button type="button" onClick={() => { setEditId(null); setName(''); setDescription(''); }} style={btnSecondary}>
            Cancel
          </button>
        )}
      </form>

      <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 14 }}>
        <thead>
          <tr style={{ background: '#f9fafb' }}>
            <th style={thStyle}>Category Name</th>
            <th style={thStyle}>Description</th>
            <th style={thStyle}>Actions</th>
          </tr>
        </thead>
        <tbody>
          {categories.map((cat) => (
            <tr key={cat.id} style={{ borderBottom: '1px solid #e5e7eb' }}>
              <td style={tdStyle}>{cat.name}</td>
              <td style={tdStyle}>{cat.description || '—'}</td>
              <td style={tdStyle}>
                <button
                  style={btnSecondary}
                  onClick={() => { setEditId(cat.id); setName(cat.name); setDescription(cat.description || ''); }}
                >
                  Edit
                </button>
                <button style={{ ...btnSecondary, marginLeft: 8, color: '#dc2626' }} onClick={() => handleDelete(cat.id)}>
                  Delete
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

const inputStyle: React.CSSProperties = {
  padding: '10px 14px',
  borderRadius: 10,
  border: '1px solid #d1d5db',
  fontSize: 14,
  minWidth: 200,
};

const thStyle: React.CSSProperties = {
  padding: '10px 12px',
  textAlign: 'left',
  borderBottom: '2px solid #e5e7eb',
  fontWeight: 700,
};

const tdStyle: React.CSSProperties = {
  padding: '10px 12px',
};

const btnPrimary: React.CSSProperties = {
  background: '#2563eb',
  color: 'white',
  border: 'none',
  borderRadius: 10,
  padding: '10px 20px',
  cursor: 'pointer',
  fontWeight: 700,
};

const btnSecondary: React.CSSProperties = {
  background: '#e5e7eb',
  color: '#111827',
  border: 'none',
  borderRadius: 10,
  padding: '8px 16px',
  cursor: 'pointer',
  fontWeight: 600,
};

import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import ComplianceTracker from './pages/ComplianceTracker';
import MasterData from './pages/MasterData';
import AuditLog from './pages/AuditLog';
import Layout from './components/Layout';

function ProtectedRoutes() {
  const { user } = useAuth();
  if (!user) return <Navigate to="/login" replace />;
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/tracker" element={<ComplianceTracker />} />
        <Route path="/master" element={<MasterData />} />
        <Route path="/audits" element={<AuditLog />} />
      </Routes>
    </Layout>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/*" element={<ProtectedRoutes />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}

