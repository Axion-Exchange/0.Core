import { z } from 'zod';

export const createMemberSchema = z.object({
  adminId: z.string().uuid(),
  department: z.string().optional(),
  title: z.string().optional(),
  timezone: z.string().max(50).optional(),
});

export const updateMemberSchema = z.object({
  department: z.string().optional(),
  title: z.string().optional(),
  timezone: z.string().max(50).optional(),
  isOnline: z.boolean().optional(),
});

export const createMeetingSchema = z.object({
  title: z.string().min(1),
  description: z.string().optional(),
  organizer: z.string().min(1),
  organizerId: z.string().uuid().optional(),
  attendees: z.array(z.string()).optional(),
  location: z.string().optional(),
  meetingUrl: z.string().url().optional(),
  startsAt: z.coerce.date(),
  endsAt: z.coerce.date(),
});

export const createScheduleSchema = z.object({
  adminId: z.string().uuid(),
  adminName: z.string().min(1),
  title: z.string().min(1),
  startsAt: z.coerce.date(),
  endsAt: z.coerce.date(),
  dayOfWeek: z.coerce.number().int().min(0).max(6).optional(),
  isRecurring: z.boolean().optional(),
  notes: z.string().optional(),
});

export const createTaskSchema = z.object({
  title: z.string().min(1),
  description: z.string().optional(),
  priority: z.enum(['LOW', 'MEDIUM', 'HIGH', 'URGENT']).default('MEDIUM'),
  assigneeId: z.string().uuid().optional(),
  assigneeName: z.string().optional(),
  dueDate: z.coerce.date().optional(),
  tags: z.array(z.string()).optional(),
});

export const updateTaskSchema = z.object({
  title: z.string().optional(),
  description: z.string().optional(),
  status: z.enum(['TODO', 'IN_PROGRESS', 'IN_REVIEW', 'COMPLETED', 'CANCELLED']).optional(),
  priority: z.enum(['LOW', 'MEDIUM', 'HIGH', 'URGENT']).optional(),
  assigneeId: z.string().uuid().optional(),
  assigneeName: z.string().optional(),
  dueDate: z.coerce.date().optional(),
  tags: z.array(z.string()).optional(),
});

export const taskQuerySchema = z.object({
  status: z.enum(['TODO', 'IN_PROGRESS', 'IN_REVIEW', 'COMPLETED', 'CANCELLED']).optional(),
  priority: z.enum(['LOW', 'MEDIUM', 'HIGH', 'URGENT']).optional(),
  assigneeId: z.string().uuid().optional(),
  page: z.coerce.number().int().min(1).default(1),
  limit: z.coerce.number().int().min(1).max(100).default(25),
});
