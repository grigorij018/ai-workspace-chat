<script lang="ts">
	import { getContext, onMount } from 'svelte';
	import dayjs from '$lib/dayjs';
	import { toast } from 'svelte-sonner';

	import { deleteMemoriesByUserId, deleteMemoryById, getMemories } from '$lib/apis/memories';
	import Spinner from '$lib/components/common/Spinner.svelte';
	import Tooltip from '$lib/components/common/Tooltip.svelte';
	import GarbageBin from '$lib/components/icons/GarbageBin.svelte';
	import XMark from '$lib/components/icons/XMark.svelte';

	const i18n = getContext('i18n');

	export let open = false;
	export let refreshKey = 0;

	let loading = false;
	let memories = [];
	let error = '';
	let lastRefreshKey = -1;

	const loadMemories = async () => {
		if (!open) return;

		loading = true;
		error = '';

		try {
			memories = await getMemories(localStorage.token);
		} catch (e) {
			error = `${e}`;
			toast.error(`${e}`);
		} finally {
			loading = false;
		}
	};

	const deleteFact = async (id: string) => {
		try {
			await deleteMemoryById(localStorage.token, id);
			memories = memories.filter((memory) => memory.id !== id);
		} catch (e) {
			toast.error(`${e}`);
		}
	};

	const clearMemory = async () => {
		try {
			await deleteMemoriesByUserId(localStorage.token);
			memories = [];
		} catch (e) {
			toast.error(`${e}`);
		}
	};

	$: if (open && lastRefreshKey === -1) {
		lastRefreshKey = refreshKey;
		loadMemories();
	}

	$: if (open && refreshKey !== lastRefreshKey) {
		lastRefreshKey = refreshKey;
		loadMemories();
	}

	$: if (!open) {
		lastRefreshKey = -1;
	}

	onMount(async () => {
		if (open) {
			await loadMemories();
		}
	});
</script>

<aside
	class={`h-full border-l border-gray-100 dark:border-gray-800 bg-white/70 dark:bg-gray-950/60 backdrop-blur-sm transition-all duration-200 overflow-hidden ${open ? 'w-[21rem] min-w-[21rem]' : 'w-0 min-w-0 border-l-0'}`}
	data-testid="memory-panel"
>
	{#if open}
		<div class="h-full flex flex-col">
			<div class="px-4 py-4 border-b border-gray-100 dark:border-gray-800 flex items-start justify-between gap-3">
				<div>
					<div class="text-sm font-semibold text-gray-900 dark:text-gray-100">
						{$i18n.t('Memory')}
					</div>
					<div class="text-xs text-gray-500 dark:text-gray-400 mt-1">
						{$i18n.t('Transparent facts available to the assistant.')}
					</div>
				</div>
				<Tooltip content={$i18n.t('Close')} placement="left">
					<button
						type="button"
						class="p-1 rounded-full hover:bg-gray-100 dark:hover:bg-gray-800 text-gray-500 dark:text-gray-300"
						on:click={() => {
							open = false;
						}}
						aria-label={$i18n.t('Close memory panel')}
					>
						<XMark className="size-4" />
					</button>
				</Tooltip>
			</div>

			<div class="px-4 py-3 border-b border-gray-100 dark:border-gray-800 flex items-center justify-between gap-2">
				<div class="text-xs text-gray-500 dark:text-gray-400">
					{memories.length} {$i18n.t('items')}
				</div>
				<button
					type="button"
					class="text-xs px-2.5 py-1.5 rounded-full bg-gray-900 text-white dark:bg-white dark:text-gray-900 disabled:opacity-50"
					on:click={clearMemory}
					disabled={loading || memories.length === 0}
				>
					{$i18n.t('Clear memory')}
				</button>
			</div>

			<div class="flex-1 overflow-y-auto px-3 py-3">
				{#if loading}
					<div class="h-full flex items-center justify-center">
						<Spinner className="size-5" />
					</div>
				{:else if error}
					<div class="text-sm text-red-500 px-2 py-3">{error}</div>
				{:else if memories.length === 0}
					<div class="text-sm text-gray-500 dark:text-gray-400 px-2 py-3">
						{$i18n.t('No memory facts stored yet.')}
					</div>
				{:else}
					<div class="flex flex-col gap-2">
						{#each memories as memory (memory.id)}
							<div class="rounded-2xl border border-gray-100 dark:border-gray-800 bg-white dark:bg-gray-900 p-3">
								<div class="flex items-start justify-between gap-3">
									<div class="min-w-0">
										<div class="text-[11px] uppercase tracking-[0.18em] text-gray-400 dark:text-gray-500">
											{memory.kind ?? 'fact'}
										</div>
										<div class="mt-1 text-sm text-gray-900 dark:text-gray-100 break-words">
											{memory.content}
										</div>
									</div>
									<Tooltip content={$i18n.t('Delete')} placement="left">
										<button
											type="button"
											class="shrink-0 p-1.5 rounded-full hover:bg-red-50 dark:hover:bg-red-950/30 text-gray-500 hover:text-red-500"
											on:click={() => deleteFact(memory.id)}
											aria-label={$i18n.t('Delete fact')}
										>
											<GarbageBin className="size-4" strokeWidth="1.75" />
										</button>
									</Tooltip>
								</div>
								<div class="mt-2 text-xs text-gray-500 dark:text-gray-400 flex items-center justify-between gap-2">
									<span>{memory.source ?? 'chat'}</span>
									<span>{dayjs(memory.updated_at * 1000).format('MMM D, HH:mm')}</span>
								</div>
							</div>
						{/each}
					</div>
				{/if}
			</div>
		</div>
	{/if}
</aside>
