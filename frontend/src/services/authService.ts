import { apiClient } from '../lib/axios';
import { AuthResponse, LoginPayload, RegisterPayload, UpdateProfilePayload, User } from '../types/auth';

export const authService = {
  async register(data: RegisterPayload): Promise<AuthResponse> {
    const res = await apiClient.post<AuthResponse>('/auth/register', data);
    return res.data;
  },

  async login(data: LoginPayload): Promise<AuthResponse> {
    const res = await apiClient.post<AuthResponse>('/auth/login', data);
    return res.data;
  },

  async logout(): Promise<void> {
    await apiClient.post('/auth/logout');
  },

  async getMe(): Promise<User> {
    const res = await apiClient.get<User>('/auth/me');
    return res.data;
  },

  async updateMe(data: UpdateProfilePayload): Promise<User> {
    const res = await apiClient.patch<User>('/auth/me', data);
    return res.data;
  },
};
