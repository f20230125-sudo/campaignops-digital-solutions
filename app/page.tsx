import Dashboard from '@/components/campaignops/dashboard';
import data from '@/public/data/dashboard.json';
import type { DashboardData } from '@/lib/campaignops';
export default function Page(){return <Dashboard data={data as DashboardData}/>;}
