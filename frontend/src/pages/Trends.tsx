import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { TrendingUp, TrendingDown } from 'lucide-react';
import { api } from '../services/api';
import type { TechStat, CompetenceStat } from '../types';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

const Trends = () => {
    const [techStats, setTechStats] = useState<TechStat[]>([]);
    const [compStats, setCompStats] = useState<CompetenceStat[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchData = async () => {
            try {
                setLoading(true);
                const [tech, comp] = await Promise.all([
                    api.getTechStats(),
                    api.getCompetenceStats(),
                ]);
                setTechStats(tech);
                setCompStats(comp);
            } catch (error) {
                console.error('Erreur lors du chargement des tendances:', error);
            } finally {
                setLoading(false);
            }
        };

        fetchData();
    }, []);

    if (loading) {
        return (
            <div className="flex items-center justify-center min-h-screen">
                <div className="text-2xl text-foreground">Chargement des tendances...</div>
            </div>
        );
    }

    return (
        <div className="space-y-6">
            <div>
                <h2 className="text-3xl font-bold tracking-tight text-foreground">Tendances & Analytics</h2>
                <p className="text-muted-foreground mt-1">Analyse approfondie du marché de l'emploi</p>
            </div>


            {/* Charts Grid */}
            <div className="grid gap-4 md:grid-cols-2">
                {/* Technologies Chart */}
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="rounded-xl border border-border bg-card shadow-sm p-6"
                >
                    <h3 className="font-semibold text-foreground mb-4 flex items-center gap-2">
                        <TrendingUp className="w-5 h-5 text-primary" />
                        Technologies les Plus Demandées
                    </h3>
                    <ResponsiveContainer width="100%" height={400}>
                        <BarChart data={techStats.slice(0, 20)}>
                            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" vertical={false} />
                            <XAxis dataKey="name" stroke="#6b7280" angle={-45} textAnchor="end" height={100} interval={0} fontSize={12} />
                            <YAxis stroke="#6b7280" />
                            <Tooltip
                                cursor={{ fill: 'transparent' }}
                                contentStyle={{
                                    backgroundColor: '#ffffff',
                                    border: '1px solid #e5e7eb',
                                    borderRadius: '8px',
                                }}
                            />
                            <Bar dataKey="count" name="Nombre d'offres" fill="#3b82f6" radius={[4, 4, 0, 0]} />
                        </BarChart>
                    </ResponsiveContainer>
                </motion.div>

                {/* Compétences Chart */}
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.1 }}
                    className="rounded-xl border border-border bg-card shadow-sm p-6"
                >
                    <h3 className="font-semibold text-foreground mb-4 flex items-center gap-2">
                        <TrendingDown className="w-5 h-5 text-purple-600" />
                        Compétences Recherchées
                    </h3>
                    {/* Increased height for more items */}
                    <ResponsiveContainer width="100%" height={600}>
                        <BarChart data={compStats.slice(0, 20)} layout="vertical" margin={{ left: 20 }}>
                            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" horizontal={false} />
                            <XAxis type="number" stroke="#6b7280" />
                            <YAxis dataKey="name" type="category" stroke="#6b7280" width={120} interval={0} fontSize={12} />
                            <Tooltip
                                cursor={{ fill: 'transparent' }}
                                contentStyle={{
                                    backgroundColor: '#ffffff',
                                    border: '1px solid #e5e7eb',
                                    borderRadius: '8px',
                                }}
                            />
                            {/* Single Solid Bar */}
                            <Bar dataKey="count" name="Nombre d'offres" fill="#a855f7" radius={[0, 4, 4, 0]} barSize={20} />
                        </BarChart>
                    </ResponsiveContainer>
                </motion.div>
            </div>

            {/* Top 20 Lists */}
            <div className="grid gap-4 md:grid-cols-2">
                <motion.div
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 0.2 }}
                    className="rounded-xl border border-border bg-card shadow-sm p-6"
                >
                    <h3 className="font-semibold text-foreground mb-4">Top 20 Technologies</h3>
                    <div className="space-y-3 h-[500px] overflow-y-auto pr-2 custom-scrollbar">
                        {techStats.slice(0, 20).map((tech, idx) => (
                            <div key={idx} className="flex items-center justify-between p-3 rounded-lg bg-secondary hover:bg-secondary/80 transition-colors">
                                <div className="flex items-center gap-3">
                                    <span className="text-xl font-bold text-primary">#{idx + 1}</span>
                                    <span className="text-foreground font-medium">{tech.name}</span>
                                </div>
                                <span className="text-primary font-semibold">{tech.count} offres</span>
                            </div>
                        ))}
                    </div>
                </motion.div>

                <motion.div
                    initial={{ opacity: 0, x: 20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 0.3 }}
                    className="rounded-xl border border-border bg-card shadow-sm p-6"
                >
                    <h3 className="font-semibold text-foreground mb-4">Top 20 Compétences</h3>
                    <div className="space-y-3 h-[500px] overflow-y-auto pr-2 custom-scrollbar">
                        {compStats.slice(0, 20).map((comp, idx) => (
                            <div key={idx} className="flex items-center justify-between p-3 rounded-lg bg-secondary hover:bg-secondary/80 transition-colors">
                                <div className="flex items-center gap-3">
                                    <span className="text-xl font-bold text-purple-600">#{idx + 1}</span>
                                    <span className="text-foreground font-medium">{comp.name}</span>
                                </div>
                                <span className="text-purple-600 font-semibold">{comp.count} offres</span>
                            </div>
                        ))}
                    </div>
                </motion.div>
            </div>
        </div>
    );
};

export default Trends;
