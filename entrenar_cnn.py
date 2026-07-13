"""
Entrenamiento de CNN para detección de fraude Nivel 2 (cambio de fuente)
Usa transfer learning con ResNet18 preentrenada en ImageNet
"""

import os
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, random_split
from torchvision import datasets, transforms, models
import matplotlib.pyplot as plt
from sklearn.metrics import classification_report, confusion_matrix
import numpy as np

# ============================================
# CONFIGURACIÓN
# ============================================

# Ruta del dataset
DATA_DIR = r'C:\Users\Lenovo\Documents\TFM\dataset_cnn'

# Hiperparámetros
BATCH_SIZE = 32
NUM_EPOCHS = 20
LEARNING_RATE = 0.001
NUM_CLASSES = 2  # limpia, fraude

# Dispositivo (GPU si está disponible)
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
print(f"Usando dispositivo: {device}")

# ============================================
# TRANSFORMACIONES DE IMÁGENES
# ============================================

# Transformaciones para entrenamiento (con aumentación de datos)
train_transforms = transforms.Compose([
    transforms.Resize((224, 224)),           # Tamaño de entrada de ResNet
    transforms.RandomRotation(degrees=5),    # Rotación leve (documentos pueden estar torcidos)
    transforms.ColorJitter(brightness=0.1, contrast=0.1),  # Variaciones de iluminación
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406],   # Normalización ImageNet
                         std=[0.229, 0.224, 0.225])
])

# Transformaciones para validación y test (sin aumentación)
val_transforms = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406],
                         std=[0.229, 0.224, 0.225])
])

# ============================================
# CARGAR DATOS
# ============================================

print("\n=== CARGANDO DATOS ===\n")

# Dataset completo (asume estructura: train/limpia, train/fraude, etc.)
train_dataset = datasets.ImageFolder(
    root=os.path.join(DATA_DIR, 'train'),
    transform=train_transforms
)

val_dataset = datasets.ImageFolder(
    root=os.path.join(DATA_DIR, 'val'),
    transform=val_transforms
)

test_dataset = datasets.ImageFolder(
    root=os.path.join(DATA_DIR, 'test'),
    transform=val_transforms
)

# DataLoaders
train_loader = DataLoader(train_dataset, batch_size=BATCH_SIZE, shuffle=True)
val_loader = DataLoader(val_dataset, batch_size=BATCH_SIZE, shuffle=False)
test_loader = DataLoader(test_dataset, batch_size=BATCH_SIZE, shuffle=False)

print(f"Train: {len(train_dataset)} imágenes")
print(f"Val: {len(val_dataset)} imágenes")
print(f"Test: {len(test_dataset)} imágenes")
print(f"Clases: {train_dataset.classes}")

# ============================================
# MODELO (Transfer Learning con ResNet18)
# ============================================

print("\n=== CREANDO MODELO ===\n")

# Cargar ResNet18 preentrenada
model = models.resnet18(weights=models.ResNet18_Weights.IMAGENET1K_V1)

# Congelar capas base (opcional: descongelar solo las últimas capas)
for param in model.parameters():
    param.requires_grad = False

# Reemplazar la última capa totalmente conectada
num_features = model.fc.in_features
model.fc = nn.Sequential(
    nn.Linear(num_features, 256),
    nn.ReLU(),
    nn.Dropout(0.2),
    nn.Linear(256, NUM_CLASSES)
)

# Mover modelo al dispositivo
model = model.to(device)

# Función de pérdida y optimizador
criterion = nn.CrossEntropyLoss()
optimizer = optim.Adam(model.fc.parameters(), lr=LEARNING_RATE)

# ============================================
# ENTRENAMIENTO
# ============================================

print("\n=== INICIANDO ENTRENAMIENTO ===\n")

train_losses = []
val_losses = []
train_accs = []
val_accs = []

best_val_acc = 0.0

for epoch in range(NUM_EPOCHS):
    # Entrenamiento
    model.train()
    running_loss = 0.0
    correct = 0
    total = 0
    
    for inputs, labels in train_loader:
        inputs, labels = inputs.to(device), labels.to(device)
        
        optimizer.zero_grad()
        outputs = model(inputs)
        loss = criterion(outputs, labels)
        loss.backward()
        optimizer.step()
        
        running_loss += loss.item()
        _, predicted = torch.max(outputs, 1)
        total += labels.size(0)
        correct += (predicted == labels).sum().item()
    
    train_loss = running_loss / len(train_loader)
    train_acc = 100 * correct / total
    train_losses.append(train_loss)
    train_accs.append(train_acc)
    
    # Validación
    model.eval()
    val_loss = 0.0
    correct = 0
    total = 0
    
    with torch.no_grad():
        for inputs, labels in val_loader:
            inputs, labels = inputs.to(device), labels.to(device)
            outputs = model(inputs)
            loss = criterion(outputs, labels)
            
            val_loss += loss.item()
            _, predicted = torch.max(outputs, 1)
            total += labels.size(0)
            correct += (predicted == labels).sum().item()
    
    val_loss = val_loss / len(val_loader)
    val_acc = 100 * correct / total
    val_losses.append(val_loss)
    val_accs.append(val_acc)
    
    print(f"Epoch {epoch+1}/{NUM_EPOCHS}")
    print(f"  Train Loss: {train_loss:.4f} | Train Acc: {train_acc:.2f}%")
    print(f"  Val Loss:   {val_loss:.4f} | Val Acc:   {val_acc:.2f}%")
    
    # Guardar mejor modelo
    if val_acc > best_val_acc:
        best_val_acc = val_acc
        torch.save(model.state_dict(), 'mejor_modelo_cnn.pth')
        print(f"  *** Mejor modelo guardado (val_acc: {val_acc:.2f}%) ***")
    print()

print("=== ENTRENAMIENTO COMPLETADO ===")

# ============================================
# EVALUACIÓN EN TEST
# ============================================

print("\n=== EVALUACIÓN EN CONJUNTO DE TEST ===\n")

model.load_state_dict(torch.load('mejor_modelo_cnn.pth'))
model.eval()

all_preds = []
all_labels = []

with torch.no_grad():
    for inputs, labels in test_loader:
        inputs, labels = inputs.to(device), labels.to(device)
        outputs = model(inputs)
        _, predicted = torch.max(outputs, 1)
        all_preds.extend(predicted.cpu().numpy())
        all_labels.extend(labels.cpu().numpy())

# Métricas
print("=== Classification Report ===")
print(classification_report(all_labels, all_preds, target_names=train_dataset.classes))

# Matriz de confusión
cm = confusion_matrix(all_labels, all_preds)
print("\n=== Matriz de Confusión ===")
print(f"                 Predicho")
print(f"               Limpia  Fraude")
print(f"Real   Limpia    {cm[0,0]:4d}    {cm[0,1]:4d}")
print(f"       Fraude    {cm[1,0]:4d}    {cm[1,1]:4d}")

accuracy = 100 * (cm[0,0] + cm[1,1]) / np.sum(cm)
print(f"\nExactitud global: {accuracy:.2f}%")

# ============================================
# GRÁFICAS DE PÉRDIDA Y PRECISIÓN
# ============================================

plt.figure(figsize=(12, 4))

plt.subplot(1, 2, 1)
plt.plot(train_losses, label='Train Loss')
plt.plot(val_losses, label='Val Loss')
plt.xlabel('Epoch')
plt.ylabel('Loss')
plt.title('Curvas de Pérdida')
plt.legend()
plt.grid(True)

plt.subplot(1, 2, 2)
plt.plot(train_accs, label='Train Accuracy')
plt.plot(val_accs, label='Val Accuracy')
plt.xlabel('Epoch')
plt.ylabel('Accuracy (%)')
plt.title('Curvas de Precisión')
plt.legend()
plt.grid(True)

plt.tight_layout()
plt.savefig('curvas_entrenamiento.png')
plt.show()

print("\n✓ Gráficas guardadas como 'curvas_entrenamiento.png'")
print("✓ Mejor modelo guardado como 'mejor_modelo_cnn.pth'")