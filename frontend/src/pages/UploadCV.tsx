import { useState, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { useDropzone } from 'react-dropzone'
import { useMutation } from '@tanstack/react-query'
import toast from 'react-hot-toast'
import { FileText, Upload, X, File, Loader2, CheckCircle, AlertCircle } from 'lucide-react'
import { cvApi } from '../services/api'

const MAX_FILE_SIZE = 10 * 1024 * 1024 // 10MB
const ACCEPTED_TYPES = {
  'application/pdf': ['.pdf'],
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
  'application/msword': ['.doc'],
  'text/plain': ['.txt'],
  'image/png': ['.png'],
  'image/jpeg': ['.jpg', '.jpeg'],
}

export default function UploadCV() {
  const navigate = useNavigate()
  const [file, setFile] = useState<File | null>(null)

  // Upload mutation
  const uploadMutation = useMutation({
    mutationFn: cvApi.upload,
    onSuccess: (data) => {
      toast.success('CV subido exitosamente')
      parseMutation.mutate(data.id)
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Error al subir el CV')
    },
  })

  // Parse mutation
  const parseMutation = useMutation({
    mutationFn: cvApi.parse,
    onSuccess: (_, cvId) => {
      toast.success('CV analizado exitosamente')
      navigate(`/dashboard/${cvId}`)
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Error al analizar el CV')
    },
  })

  const isProcessing = uploadMutation.isPending || parseMutation.isPending

  const onDrop = useCallback((acceptedFiles: File[], rejectedFiles: any[]) => {
    if (rejectedFiles.length > 0) {
      const error = rejectedFiles[0].errors[0]
      if (error.code === 'file-too-large') {
        toast.error('Archivo demasiado grande. Máximo 10MB')
      } else if (error.code === 'file-invalid-type') {
        toast.error('Tipo de archivo no soportado')
      } else {
        toast.error(error.message)
      }
      return
    }

    if (acceptedFiles.length > 0) {
      setFile(acceptedFiles[0])
    }
  }, [])

  const { getRootProps, getInputProps, isDragActive, isDragReject } = useDropzone({
    onDrop,
    accept: ACCEPTED_TYPES,
    maxSize: MAX_FILE_SIZE,
    multiple: false,
    disabled: isProcessing,
  })

  const handleSubmit = () => {
    if (!file) {
      toast.error('Por favor selecciona un archivo')
      return
    }
    uploadMutation.mutate(file)
  }

  const clearFile = () => {
    setFile(null)
  }

  const getFileIcon = (fileName: string) => {
    const extension = fileName.split('.').pop()?.toLowerCase()
    switch (extension) {
      case 'pdf':
        return <FileText className="w-12 h-12 text-red-500" />
      case 'docx':
      case 'doc':
        return <FileText className="w-12 h-12 text-blue-500" />
      case 'txt':
        return <FileText className="w-12 h-12 text-gray-500" />
      case 'png':
      case 'jpg':
      case 'jpeg':
        return <File className="w-12 h-12 text-purple-500" />
      default:
        return <File className="w-12 h-12 text-gray-500" />
    }
  }

  const getStatusMessage = () => {
    if (uploadMutation.isPending) {
      return 'Subiendo CV...'
    }
    if (parseMutation.isPending) {
      return 'La IA está analizando tu CV... Esto puede tomar un momento'
    }
    return ''
  }

  return (
    <div className="max-w-2xl mx-auto">
      <div className="mb-8 text-center">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Sube tu CV</h1>
        <p className="text-gray-600">
          Soportamos PDF, Word, TXT e imágenes
        </p>
      </div>

      {!file ? (
        <div
          {...getRootProps()}
          className={`
            border-2 border-dashed rounded-xl p-12 text-center cursor-pointer transition-all
            ${isDragActive ? 'border-primary-500 bg-primary-50' : 'border-gray-300'}
            ${isDragReject ? 'border-red-500 bg-red-50' : ''}
            ${isProcessing ? 'opacity-50 cursor-not-allowed' : 'hover:border-primary-400 hover:bg-gray-50'}
          `}
        >
          <input {...getInputProps()} />

          <div className="mb-4">
            <div className="w-16 h-16 bg-primary-100 rounded-full flex items-center justify-center mx-auto">
              <Upload className={`w-8 h-8 ${isDragActive ? 'text-primary-600' : 'text-primary-500'}`} />
            </div>
          </div>

          <p className="text-lg font-medium text-gray-900 mb-1">
            {isDragActive ? 'Suelta el archivo aquí' : 'Arrastra tu CV aquí'}
          </p>
          <p className="text-gray-500 mb-4">
            o haz clic para seleccionar un archivo
          </p>

          <div className="flex flex-wrap items-center justify-center gap-2 text-sm text-gray-400">
            <span className="px-2 py-1 bg-gray-100 rounded">PDF</span>
            <span className="px-2 py-1 bg-gray-100 rounded">DOCX</span>
            <span className="px-2 py-1 bg-gray-100 rounded">TXT</span>
            <span className="px-2 py-1 bg-gray-100 rounded">PNG/JPG</span>
          </div>

          <p className="text-xs text-gray-400 mt-4">
            Tamaño máximo: 10MB
          </p>
        </div>
      ) : (
        <div className="card">
          <div className="flex items-start gap-4">
            {getFileIcon(file.name)}

            <div className="flex-1">
              <h3 className="font-medium text-gray-900">{file.name}</h3>
              <p className="text-sm text-gray-500">
                {(file.size / 1024).toFixed(1)} KB
              </p>

              {isProcessing ? (
                <div className="mt-4">
                  <div className="flex items-center gap-2 text-primary-600">
                    <Loader2 className="w-5 h-5 animate-spin" />
                    <span className="text-sm">{getStatusMessage()}</span>
                  </div>
                  <div className="mt-2 h-2 bg-gray-200 rounded-full overflow-hidden">
                    <div className="h-full bg-primary-500 animate-pulse" style={{ width: uploadMutation.isPending ? '50%' : '100%' }} />
                  </div>
                </div>
              ) : (
                <div className="mt-4 flex items-center gap-2 text-green-600">
                  <CheckCircle className="w-5 h-5" />
                  <span className="text-sm">Listo para procesar</span>
                </div>
              )}
            </div>

            {!isProcessing && (
              <button
                onClick={clearFile}
                className="p-1 text-gray-400 hover:text-red-500 transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            )}
          </div>
        </div>
      )}

      {file && !isProcessing && (
        <div className="mt-6 flex gap-4">
          <button
            onClick={clearFile}
            className="btn-outline flex-1"
          >
            Cambiar archivo
          </button>
          <button
            onClick={handleSubmit}
            className="btn-primary flex-1 gap-2"
          >
            Procesar con IA
            <FileText className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* Info box */}
      <div className="mt-8 bg-blue-50 border border-blue-200 rounded-xl p-4">
        <div className="flex gap-3">
          <AlertCircle className="w-5 h-5 text-blue-500 flex-shrink-0 mt-0.5" />
          <div className="text-sm text-blue-800">
            <p className="font-medium mb-1">¿Qué sucede después?</p>
            <p>
              1. Subimos tu CV de forma segura<br />
              2. Nuestra IA extrae tu información (nombre, experiencia, habilidades)<br />
              3. Puedes revisar y editar la información extraída<br />
              4. ¡Listo para buscar empleos!
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
