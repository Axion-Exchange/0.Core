import { prisma } from '../lib/db.js';
import type { Prisma, TaskStatus, TaskPriority, MeetingStatus } from '@prisma/client';

export class TeamService {
  // ── Members ────────────────────────────────────────

  async listMembers() {
    return prisma.teamMember.findMany({
      orderBy: { joinedAt: 'asc' },
    });
  }

  async createMember(data: { adminId: string; department?: string; title?: string; timezone?: string }) {
    return prisma.teamMember.create({ data: data as any });
  }

  async updateMember(id: string, data: Partial<{ department: string; title: string; timezone: string; isOnline: boolean }>) {
    return prisma.teamMember.update({ where: { id }, data });
  }

  async deleteMember(id: string) {
    return prisma.teamMember.delete({ where: { id } });
  }

  // ── Meetings ───────────────────────────────────────

  async listMeetings(filters?: { status?: MeetingStatus; from?: Date; to?: Date; page?: number; limit?: number }) {
    const page = filters?.page ?? 1;
    const limit = filters?.limit ?? 25;
    const where: Prisma.MeetingWhereInput = {};

    if (filters?.status) where.status = filters.status;
    if (filters?.from || filters?.to) {
      where.startsAt = {};
      if (filters?.from) where.startsAt.gte = filters.from;
      if (filters?.to) where.startsAt.lte = filters.to;
    }

    const [data, total] = await Promise.all([
      prisma.meeting.findMany({
        where,
        orderBy: { startsAt: 'asc' },
        skip: (page - 1) * limit,
        take: limit,
      }),
      prisma.meeting.count({ where }),
    ]);

    return { data, total, page, limit };
  }

  async createMeeting(data: { title: string; description?: string; organizer: string; organizerId?: string; attendees?: string[]; location?: string; meetingUrl?: string; startsAt: Date; endsAt: Date }) {
    return prisma.meeting.create({ data: { ...data, attendees: data.attendees ?? [] } as any });
  }

  async updateMeeting(id: string, data: Record<string, unknown>) {
    return prisma.meeting.update({ where: { id }, data: data as any });
  }

  async deleteMeeting(id: string) {
    return prisma.meeting.delete({ where: { id } });
  }

  // ── Schedules ──────────────────────────────────────

  async listSchedules(filters?: { adminId?: string; from?: Date; to?: Date }) {
    const where: Prisma.ScheduleWhereInput = {};

    if (filters?.adminId) where.adminId = filters.adminId;
    if (filters?.from || filters?.to) {
      where.startsAt = {};
      if (filters?.from) where.startsAt.gte = filters.from;
      if (filters?.to) where.startsAt.lte = filters.to;
    }

    return prisma.schedule.findMany({ where, orderBy: { startsAt: 'asc' } });
  }

  async createSchedule(data: { adminId: string; adminName: string; title: string; startsAt: Date; endsAt: Date; dayOfWeek?: number; isRecurring?: boolean; notes?: string }) {
    return prisma.schedule.create({ data: data as any });
  }

  async updateSchedule(id: string, data: Record<string, unknown>) {
    return prisma.schedule.update({ where: { id }, data: data as any });
  }

  async deleteSchedule(id: string) {
    return prisma.schedule.delete({ where: { id } });
  }

  // ── Tasks ──────────────────────────────────────────

  async listTasks(filters?: { status?: TaskStatus; priority?: TaskPriority; assigneeId?: string; page?: number; limit?: number }) {
    const page = filters?.page ?? 1;
    const limit = filters?.limit ?? 25;
    const where: Prisma.TaskWhereInput = {};

    if (filters?.status) where.status = filters.status;
    if (filters?.priority) where.priority = filters.priority;
    if (filters?.assigneeId) where.assigneeId = filters.assigneeId;

    const [data, total] = await Promise.all([
      prisma.task.findMany({
        where,
        orderBy: [{ priority: 'desc' }, { createdAt: 'desc' }],
        skip: (page - 1) * limit,
        take: limit,
      }),
      prisma.task.count({ where }),
    ]);

    return { data, total, page, limit };
  }

  async createTask(data: { title: string; description?: string; priority?: string; assigneeId?: string; assigneeName?: string; reporterId?: string; reporterName?: string; dueDate?: Date; tags?: string[] }) {
    return prisma.task.create({ data: { ...data, tags: data.tags ?? [] } as any });
  }

  async updateTask(id: string, data: Record<string, unknown>) {
    const update: Record<string, unknown> = { ...data };
    if (data['status'] === 'COMPLETED') update['completedAt'] = new Date();
    return prisma.task.update({ where: { id }, data: update as any });
  }

  async deleteTask(id: string) {
    return prisma.task.delete({ where: { id } });
  }
}

export const teamService = new TeamService();
