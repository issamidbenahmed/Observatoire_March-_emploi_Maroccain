import { motion } from 'framer-motion';
import { useEffect, useState } from 'react';
import { Briefcase, Building2, Clock, TrendingUp } from 'lucide-react';
import { api } from '../services/api';
import type { GlobalStats, TechStat, RegionStat } from '../types';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import { ExportButton } from '../components/ExportButton';
import { MoroccoMap } from '../components/MoroccoMap';

const COLORS = ['#0891b2', '#0ea5e9', '#3b82f6', '#6366f1', '#8b5cf6', '#a855f7', '#ec4899', '#f43f5e'];

const Dashboard = () => {
    const [stats, setStats] = useState<GlobalStats | null>(null);
    const [techStats, setTechStats] = useState<TechStat[]>([]);
    const [regionStats, setRegionStats] = useState<RegionStat[]>([]);
    const [companyStats, setCompanyStats] = useState<{ name: string; count: number }[]>([]);
    const [sourceStats, setSourceStats] = useState<{ name: string; count: number }[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchData = async () => {
            try {
                setLoading(true);
                const [globalData, techData, regionData, companyData, sourceData] = await Promise.all([
                    api.getGlobalStats(),
                    api.getTechStats(),
                    api.getRegionStats(),
                    api.getCompanyStats(),
                    api.getSourceStats(),
                ]);

                setStats(globalData);
                setTechStats(techData.slice(0, 10)); // Top 10
                setRegionStats(regionData); // Toutes les villes pour la carte
                setCompanyStats(companyData.slice(0, 10)); // Top 10
                setSourceStats(sourceData);
            } catch (error) {
                console.error('Erreur lors du chargement des données:', error);
            } finally {
                setLoading(false);
            }
        };

        fetchData();
        // Rafraîchir toutes les 30 secondes
        const interval = setInterval(fetchData, 200000);
        return () => clearInterval(interval);
    }, []);

    const statCards = [
        {
            title: 'Total Offres',
            value: stats?.total_jobs || 0,
            icon: Briefcase,
            color: 'from-cyan-500 to-blue-500',
        },
        {
            title: 'Entreprises',
            value: stats?.total_companies || 0,
            icon: Building2,
            color: 'from-purple-500 to-pink-500',
        },
        {
            title: 'Nouveaux (24h)',
            value: stats?.new_jobs_24h || 0,
            icon: TrendingUp,
            color: 'from-green-500 to-emerald-500',
        },
        {
            title: 'Dernière MAJ',
            value: stats?.last_update ? new Date(stats.last_update).toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' }) : '--:--',
            icon: Clock,
            color: 'from-orange-500 to-red-500',
        },
    ];

    if (loading) {
        return (
            <div className="flex items-center justify-center min-h-screen">
                <div className="text-2xl text-foreground">Chargement des données...</div>
            </div>
        );
    }

    return (
        <div className="space-y-6">
            <div className="flex justify-between items-end">
                <div>
                    <h2 className="text-3xl font-bold tracking-tight text-foreground">Dashboard</h2>
                    <p className="text-muted-foreground mt-1">Vue d'ensemble du marché de l'emploi en temps réel</p>
                </div>
                <ExportButton />
            </div>

            {/* Stats Cards */}
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
                {statCards.map((stat, i) => {
                    const Icon = stat.icon;
                    return (
                        <motion.div
                            key={i}
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: i * 0.1 }}
                            className="p-6 rounded-xl border border-border bg-card shadow-sm hover:shadow-md transition-all group"
                        >
                            <div className="flex items-center justify-between">
                                <div>
                                    <p className="text-sm font-medium text-muted-foreground">{stat.title}</p>
                                    <h3 className="text-2xl font-bold mt-2 text-foreground">{stat.value}</h3>
                                </div>
                                <div className={`p-3 rounded-lg bg-gradient-to-br ${stat.color} opacity-90 group-hover:opacity-100 transition-opacity`}>
                                    <Icon className="w-6 h-6 text-white" />
                                </div>
                            </div>
                        </motion.div>
                    );
                })}
            </div>

            {/* Charts Grid */}
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-7">
                {/* Top Technologies */}
                <motion.div
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 0.4 }}
                    className="col-span-4 rounded-xl border border-border bg-card shadow-sm p-6"
                >
                    <h3 className="font-semibold text-foreground mb-4">Top Technologies Demandées</h3>
                    <ResponsiveContainer width="100%" height={300}>
                        <BarChart data={techStats}>
                            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                            <XAxis dataKey="name" stroke="#6b7280" />
                            <YAxis stroke="#6b7280" />
                            <Tooltip
                                contentStyle={{
                                    backgroundColor: '#ffffff',
                                    border: '1px solid #e5e7eb',
                                    borderRadius: '8px',
                                }}
                            />
                            <Bar dataKey="count" fill="url(#colorTech)" radius={[8, 8, 0, 0]} />
                            <defs>
                                <linearGradient id="colorTech" x1="0" y1="0" x2="0" y2="1">
                                    <stop offset="0%" stopColor="#06b6d4" stopOpacity={0.8} />
                                    <stop offset="100%" stopColor="#3b82f6" stopOpacity={0.3} />
                                </linearGradient>
                            </defs>
                        </BarChart>
                    </ResponsiveContainer>
                </motion.div>

                {/* Top Companies List */}
                <motion.div
                    initial={{ opacity: 0, x: 20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 0.5 }}
                    className="col-span-3 rounded-xl border border-border bg-card shadow-sm p-6"
                >
                    <h3 className="font-semibold text-foreground mb-4">Top Entreprises</h3>
                    <div className="space-y-4 pr-2">
                        {companyStats.map((company, idx) => (
                            <div key={idx} className="flex items-center justify-between group">
                                <span className="text-sm font-medium text-foreground truncate max-w-[200px]" title={company.name}>
                                    {company.name}
                                </span>
                                <div className="flex items-center gap-3">
                                    <div className="w-24 h-2 bg-secondary rounded-full overflow-hidden">
                                        <div
                                            className="h-full bg-gradient-to-r from-purple-500 to-pink-500 rounded-full"
                                            style={{ width: `${(company.count / (companyStats[0]?.count || 1)) * 100}%` }}
                                        />
                                    </div>
                                    <span className="text-sm font-bold text-foreground w-6 text-right">{company.count}</span>
                                </div>
                            </div>
                        ))}
                    </div>
                </motion.div>

                {/* Sources Distribution Pie Chart */}
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.6 }}
                    className="col-span-2 rounded-xl border border-border bg-card shadow-sm p-6"
                >
                    <h3 className="font-semibold text-foreground mb-4">Répartition par Source</h3>
                    <div className="h-[300px] md:h-[400px] w-full">
                        <ResponsiveContainer width="100%" height="100%">
                            <PieChart>
                                <Pie
                                    data={sourceStats}
                                    cx="50%"
                                    cy="50%"
                                    innerRadius="60%"
                                    outerRadius="80%"
                                    fill="#8884d8"
                                    paddingAngle={5}
                                    dataKey="count"
                                >
                                    {sourceStats.map((_, index) => (
                                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                                    ))}
                                </Pie>
                                <Tooltip />
                            </PieChart>
                        </ResponsiveContainer>
                    </div>
                    <div className="flex flex-wrap gap-2 justify-center mt-4">
                        {sourceStats.map((entry, index) => (
                            <div key={index} className="flex items-center gap-1.5">
                                <div className="w-3 h-3 rounded-full" style={{ backgroundColor: COLORS[index % COLORS.length] }} />
                                <span className="text-xs text-muted-foreground">{entry.name} ({entry.count})</span>
                            </div>
                        ))}
                    </div>
                </motion.div>

                {/* Morocco Map */}
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.7 }}
                    className="col-span-5 rounded-xl border border-border bg-card shadow-sm"
                    style={{ minHeight: '750px' }}
                >
                    <MoroccoMap cities={regionStats} />
                </motion.div>
            </div>
        </div>
    );
};

export default Dashboard;
