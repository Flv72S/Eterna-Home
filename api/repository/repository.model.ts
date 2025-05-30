import mongoose, { Document, Schema } from 'mongoose';

export interface IRepository extends Document {
  name: string;
  ownerId: string;
  description?: string;
  tags: string[];
  createdAt: Date;
  updatedAt: Date;
}

const repositorySchema = new Schema<IRepository>(
  {
    name: {
      type: String,
      required: [true, 'Name is required'],
      trim: true,
    },
    ownerId: {
      type: String,
      required: [true, 'Owner ID is required'],
    },
    description: {
      type: String,
      trim: true,
    },
    tags: [{
      type: String,
      trim: true,
    }],
  },
  {
    timestamps: true,
  }
);

// Indexes
repositorySchema.index({ ownerId: 1 });
repositorySchema.index({ tags: 1 });

export const Repository = mongoose.model<IRepository>('Repository', repositorySchema); 