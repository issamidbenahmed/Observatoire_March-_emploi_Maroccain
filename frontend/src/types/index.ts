// Types pour l'application
export interface Job {
    id: number;
    title: string;
    company: string;
    location: string;
    skills: string[];
    technologies: string[];
    date_posted: string;
    source_site: string;
    url_offre: string;
    salaire?: string;
}

export interface GlobalStats {
    total_jobs: number;
    total_companies: number;
    last_update: string | null;
    new_jobs_24h: number;
}

export interface TechStat {
    name: string;
    count: number;
}

export interface CompetenceStat {
    name: string;
    count: number;
}

export interface RegionStat {
    name: string;
    count: number;
}
