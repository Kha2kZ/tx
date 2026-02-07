import { useQuery } from "@tanstack/react-query";
import { api } from "@shared/routes";

export function useLeaderboard() {
  return useQuery({
    queryKey: [api.leaderboard.list.path],
    queryFn: async () => {
      const res = await fetch(api.leaderboard.list.path);
      if (!res.ok) throw new Error("Failed to fetch leaderboard");
      const data = await res.json();
      return api.leaderboard.list.responses[200].parse(data);
    },
    // Refresh every minute to keep ranks updated
    refetchInterval: 60000, 
  });
}
