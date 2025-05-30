import { Repository, IRepository } from './repository.model';

interface CreateRepositoryInput {
  name: string;
  ownerId: string;
  description?: string;
  tags?: string[];
}

interface UpdateRepositoryInput {
  name?: string;
  description?: string;
  tags?: string[];
}

export async function createRepository(data: CreateRepositoryInput): Promise<IRepository> {
  if (!data.name) {
    throw new Error('Name is required');
  }
  if (!data.ownerId) {
    throw new Error('Owner ID is required');
  }

  const repository = new Repository({
    name: data.name,
    ownerId: data.ownerId,
    description: data.description,
    tags: data.tags || [],
  });

  return repository.save();
}

export async function getRepository(id: string): Promise<IRepository | null> {
  return Repository.findById(id);
}

export async function updateRepository(
  id: string,
  updates: UpdateRepositoryInput
): Promise<IRepository> {
  const repository = await Repository.findById(id);
  
  if (!repository) {
    throw new Error('Repository not found');
  }

  Object.assign(repository, updates);
  return repository.save();
}

export async function deleteRepository(id: string): Promise<void> {
  const repository = await Repository.findById(id);
  
  if (!repository) {
    throw new Error('Repository not found');
  }

  await repository.deleteOne();
}

export async function listRepositories(ownerId: string): Promise<IRepository[]> {
  return Repository.find({ ownerId }).sort({ createdAt: -1 });
}

export async function searchRepositories(query: string): Promise<IRepository[]> {
  return Repository.find({
    $or: [
      { name: { $regex: query, $options: 'i' } },
      { description: { $regex: query, $options: 'i' } },
      { tags: { $in: [new RegExp(query, 'i')] } },
    ],
  }).sort({ createdAt: -1 });
} 