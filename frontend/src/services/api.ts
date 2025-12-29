// Service API pour communiquer avec le backend
import type { Job, GlobalStats, TechStat, CompetenceStat, RegionStat } from '../types';

const API_BASE_URL = 'http://localhost:5000/api';

export const api = {
    // Récupérer les statistiques globales
    async getGlobalStats(): Promise<GlobalStats> {
        const response = await fetch(`${API_BASE_URL}/stats/global`);
        if (!response.ok) throw new Error('Failed to fetch global stats');
        return response.json();
    },

    // Récupérer les jobs avec filtres
    async getJobs(params?: {
        page?: number;
        per_page?: number;
        city?: string;
        company?: string;
        tech?: string;
    }): Promise<{ jobs: Job[]; total: number; pages: number; current_page: number }> {
        const queryParams = new URLSearchParams();
        if (params?.page) queryParams.append('page', params.page.toString());
        if (params?.per_page) queryParams.append('per_page', params.per_page.toString());
        if (params?.city) queryParams.append('city', params.city);
        if (params?.company) queryParams.append('company', params.company);
        if (params?.tech) queryParams.append('tech', params.tech);

        const response = await fetch(`${API_BASE_URL}/jobs?${queryParams}`);
        if (!response.ok) throw new Error('Failed to fetch jobs');
        return response.json();
    },

    // Récupérer un job par ID
    async getJobById(id: number): Promise<Job> {
        const response = await fetch(`${API_BASE_URL}/jobs/${id}`);
        if (!response.ok) throw new Error('Failed to fetch job');
        return response.json();
    },

    // Récupérer les statistiques des technologies
    async getTechStats(): Promise<TechStat[]> {
        const response = await fetch(`${API_BASE_URL}/stats/technologies`);
        if (!response.ok) throw new Error('Failed to fetch tech stats');
        return response.json();
    },

    // Récupérer les statistiques des compétences
    async getCompetenceStats(): Promise<CompetenceStat[]> {
        const response = await fetch(`${API_BASE_URL}/stats/competences`);
        if (!response.ok) throw new Error('Failed to fetch competence stats');
        return response.json();
    },

    // Récupérer les statistiques par région
    async getRegionStats(): Promise<RegionStat[]> {
        const response = await fetch(`${API_BASE_URL}/stats/regions`);
        if (!response.ok) throw new Error('Failed to fetch region stats');
        return response.json();
    },

    // Lancer le scraping manuel
    async runScraping(): Promise<{ status: string; message: string }> {
        const response = await fetch(`${API_BASE_URL}/sync/run`, { method: 'POST' });
        if (!response.ok) throw new Error('Failed to run scraping');
        return response.json();
    },

    // Récupérer le statut du scraping
    async getScrapingStatus(): Promise<{ status: string; last_run?: string; jobs_added?: number }> {
        const response = await fetch(`${API_BASE_URL}/sync/status`);
        if (!response.ok) throw new Error('Failed to fetch scraping status');
        return response.json();
    },

    // Récupérer les stats entreprises
    async getCompanyStats(): Promise<{ name: string; count: number }[]> {
        const response = await fetch(`${API_BASE_URL}/stats/companies`);
        if (!response.ok) throw new Error('Failed to fetch company stats');
        return response.json();
    },

    // Récupérer les stats sources
    async getSourceStats(): Promise<{ name: string; count: number }[]> {
        const response = await fetch(`${API_BASE_URL}/stats/sources`);
        if (!response.ok) throw new Error('Failed to fetch source stats');
        return response.json();
    },

    // URL pour l'export CSV
    getExportUrl(): string {
        return `${API_BASE_URL}/jobs/export`;
    },

    // --- HISTORICAL & ANALYTICS ---

    async getJobsHistory(): Promise<{ month: string; count: number }[]> {
        const response = await fetch(`${API_BASE_URL}/stats/history/jobs`);
        if (!response.ok) throw new Error('Failed to fetch jobs history');
        return response.json();
    },

    async getTechHistory(): Promise<Record<string, number | string>[]> {
        const response = await fetch(`${API_BASE_URL}/stats/history/technologies`);
        if (!response.ok) throw new Error('Failed to fetch tech history');
        return response.json();
    },

    async runEnhancedScraping(): Promise<{ status: string; message: string }> {
        const response = await fetch(`${API_BASE_URL}/sync/enhanced`, { method: 'POST' });
        if (!response.ok) throw new Error('Failed to run enhanced scraping');
        return response.json();
    }
};
